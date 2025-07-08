import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = '7967604234:AAH9kR3iqNYZmTFYufhswI2NurEsInKpvNs'
TMDB_API_KEY = '483de4593d2f29b03b6f91ec412f3230'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🍿 *Welcome to MovieVerse!*\n\n"
                                   "🎥 Just send me any movie name and I'll fetch:\n"
                                   "⭐ IMDb Ratings\n🎬 Cast & Director\n📆 Release Date\n🖼️ Poster\n\n"
                                   "_Let's make your movie page amazing!_",
                                   parse_mode="Markdown")

def get_movie_data(query):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}'
    response = requests.get(url).json()
    if not response['results']:
        return None
    movie = response['results'][0]
    movie_id = movie['id']
    details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits'
    details = requests.get(details_url).json()

    title = details.get('title', 'N/A')
    year = details.get('release_date', '')[:4]
    rating = details.get('vote_average', 'N/A')
    release = details.get('release_date', 'N/A')
    genre = ', '.join([g['name'] for g in details.get('genres', [])])
    poster_url = f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}" if details.get('poster_path') else None
    cast = ', '.join([c['name'] for c in details['credits']['cast'][:3]]) if 'credits' in details else 'N/A'
    director = next((c['name'] for c in details['credits']['crew'] if c['job'] == 'Director'), 'N/A')
    hashtags = '#' + title.replace(' ', '') + ' #' + genre.replace(', ', ' #')
    summary = f"""🎬 *{title} ({year})*\n⭐ IMDb: {rating}/10\n📅 Release: {release}\n🎭 Cast: {cast}\n🎬 Director: {director}\n🧾 Genre: {genre}\n🏷️ {hashtags}"""
    return summary, poster_url

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.chat.send_action("typing")
    data = get_movie_data(query)
    if data:
        text, poster = data
        if poster:
            await update.message.reply_photo(photo=poster, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Movie not found. Try another name.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()
