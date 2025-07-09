import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = '7967604234:AAH9kR3iqNYZmTFYufhswI2NurEsInKpvNs'
TMDB_API_KEY = '483de4593d2f29b03b6f91ec412f3230'

GENRE_MAP = {
    "action": 28,
    "comedy": 35,
    "horror": 27,
    "romance": 10749,
    "sci-fi": 878,
    "thriller": 53
}

YEAR_LIST = ['2024', '2023', '2022', '2021', '2020']

# ─────────────────────── START ─────────────────────── #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genre_buttons = [
        [InlineKeyboardButton("🎬 Action", callback_data='genre_action'),
         InlineKeyboardButton("😂 Comedy", callback_data='genre_comedy')],
        [InlineKeyboardButton("👻 Horror", callback_data='genre_horror'),
         InlineKeyboardButton("❤️ Romance", callback_data='genre_romance')],
        [InlineKeyboardButton("🚀 Sci-Fi", callback_data='genre_sci-fi'),
         InlineKeyboardButton("🔪 Thriller", callback_data='genre_thriller')],
    ]
    reply_markup = InlineKeyboardMarkup(genre_buttons)
    await update.message.reply_text("🎯 *Choose a Genre:*", parse_mode="Markdown", reply_markup=reply_markup)

# ─────────────────────── CALLBACK HANDLER ─────────────────────── #
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("genre_"):
        genre_key = data.split("_")[1]
        genre_id = GENRE_MAP.get(genre_key)

        if genre_id:
            context.user_data['selected_genre'] = genre_id
            year_buttons = [[InlineKeyboardButton(f"{y}", callback_data=f"year_{y}")] for y in YEAR_LIST]
            year_buttons.append([InlineKeyboardButton("🔁 Back to Genres", callback_data="back_genres")])
            reply_markup = InlineKeyboardMarkup(year_buttons)
            await query.edit_message_text(f"📅 *Select a Year for {genre_key.capitalize()} Movies:*", parse_mode="Markdown", reply_markup=reply_markup)

    elif data.startswith("year_"):
        year = data.split("_")[1]
        genre_id = context.user_data.get('selected_genre')

        movies = get_movies_by_genre_year(genre_id, year)
        if movies:
            await query.edit_message_text(f"🎬 *Top {year} Movies:*", parse_mode="Markdown")
            for m in movies:
                await send_movie_details(query.message.chat_id, m, context)
        else:
            await query.edit_message_text("❌ No movies found for this genre & year.")

    elif data == "back_genres":
        await start(query, context)

# ─────────────────────── MOVIE DATA ─────────────────────── #
def get_movies_by_genre_year(genre_id, year):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&primary_release_year={year}&sort_by=popularity.desc'
    res = requests.get(url).json()
    return [m['id'] for m in res.get('results', [])[:10]]

def get_movie_details(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos'
    res = requests.get(url).json()

    title = res.get('title', 'N/A')
    year = res.get('release_date', '')[:4]
    rating = res.get('vote_average', 'N/A')
    release = res.get('release_date', 'N/A')
    genre = ', '.join([g['name'] for g in res.get('genres', [])])
    lang = res.get('original_language', 'N/A').upper()
    poster_url = f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}" if res.get('poster_path') else None
    cast = ', '.join([c['name'] for c in res['credits'].get('cast', [])[:3]]) or 'N/A'
    director = next((c['name'] for c in res['credits'].get('crew', []) if c['job'] == 'Director'), 'N/A')
    hashtags = '#' + title.replace(' ', '') + ' #' + genre.replace(', ', ' #')

    trailer = next((v for v in res.get('videos', {}).get('results', []) if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)
    trailer_link = f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else None

    summary = f"""🎬 *{title} ({year})*\n🗣 Language: {lang}\n⭐ IMDb: {rating}/10\n📅 Release: {release}\n🎭 Cast: {cast}\n🎬 Director: {director}\n🧾 Genre: {genre}\n🏷️ {hashtags}"""
    if trailer_link:
        summary += f"\n▶️ [Watch Trailer]({trailer_link})"

    return summary, poster_url

async def send_movie_details(chat_id, movie_id, context):
    summary, poster_url = get_movie_details(movie_id)
    if poster_url:
        keyboard = [[InlineKeyboardButton("📥 Download Poster", url=poster_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(chat_id=chat_id, photo=poster_url, caption=summary, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")

# ─────────────────────── FALLBACK SEARCH ─────────────────────── #
def search_by_name(name):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}'
    res = requests.get(url).json()
    return [m['id'] for m in res.get('results', [])[:3]]

async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.chat.send_action("typing")
    ids = search_by_name(query)
    if not ids:
        await update.message.reply_text("❌ Movie not found.")
    for movie_id in ids:
        await send_movie_details(update.message.chat_id, movie_id, context)

# ─────────────────────── MAIN ─────────────────────── #
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))
    print("✅ MovieVerse v3.0 is running...")
    app.run_polling()
