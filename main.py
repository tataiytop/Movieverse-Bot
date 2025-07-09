import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = '7967604234:AAH9kR3iqNYZmTFYufhswI2NurEsInKpvNs'
TMDB_API_KEY = '483de4593d2f29b03b6f91ec412f3230'

GENRE_KEYBOARD = [
    ["🎬 Action", "👻 Horror"],
    ["❤️ Romance", "😂 Comedy"],
    ["🔪 Thriller", "🚀 Sci-Fi"]
]

GENRE_MAP = {
    "🎬 Action": 28,
    "👻 Horror": 27,
    "❤️ Romance": 10749,
    "😂 Comedy": 35,
    "🔪 Thriller": 53,
    "🚀 Sci-Fi": 878
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(GENRE_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "🍿 *Welcome to MovieVerse!*\n\n"
        "🎥 Just send me any movie name and I'll fetch:\n"
        "⭐ IMDb Ratings\n🎬 Cast & Director\n📆 Release Date\n🖼️ Poster\n\n"
        "_Let's make your movie page amazing!_",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

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

def search_by_name(query):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}'
    res = requests.get(url).json()
    return [m['id'] for m in res.get('results', [])[:3]]

def get_movies_by_genre(genre_id):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&sort_by=popularity.desc'
    res = requests.get(url).json()
    return [m['id'] for m in res.get('results', [])[:10]]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    chat_id = update.message.chat_id

    if msg in GENRE_MAP:
        genre_id = GENRE_MAP[msg]
        movies = get_movies_by_genre(genre_id)
        await update.message.reply_text(f"🎯 Top 10 {msg} Movies:")
        for m in movies:
            await send_movie(chat_id, m, context)
    else:
        movies = search_by_name(msg)
        if not movies:
            await update.message.reply_text("❌ Movie not found. Try a different name.")
        for m in movies:
            await send_movie(chat_id, m, context)

async def send_movie(chat_id, movie_id, context):
    summary, poster_url = get_movie_details(movie_id)
    if poster_url:
        await context.bot.send_photo(chat_id=chat_id, photo=poster_url, caption=summary, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ MovieVerse v3.1 is running with Reply Buttons")
    app.run_polling()
