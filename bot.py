import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from config import API_TOKEN, ADMIN_IDS
from admin_handlers import show_admin_menu
from user_handlers import setup as setup_user_handlers, show_user_menu
from channel_handlers import setup as setup_channel_handlers
from content_handlers import setup as setup_content_handlers
from database_manager import DatabaseManager
from utils import print_colored_logo
from models import User, Channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = DatabaseManager('bot_database.db')

async def on_startup(dispatcher: Dispatcher):
    logger.info("Bot is starting...")
    print_colored_logo()

async def on_shutdown(dispatcher: Dispatcher):
    logger.info("Bot is shutting down...")
    await bot.session.close()

async def start_command(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await show_admin_menu(message)
    else:
        await show_user_menu(message)

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    if isinstance(exception, TelegramBadRequest) and "query is too old" in str(exception):
        return True
    logging.error(f"Unhandled exception: {exception}")
    return False

async def add_channel(message: types.Message):
    # Implementazione della nuova funzionalità di aggiunta canali
    post_link = message.text
    try:
        channel_id = post_link.split('/')[-2]
        await message.reply("Inserisci il nome del pulsante:")
        # Qui dovresti gestire la risposta dell'utente per il nome del pulsante
        # e poi chiedere il link di iscrizione
    except:
        await message.reply("Link del post non valido. Riprova.")

async def main():
    setup_admin_handlers(dp)
    setup_user_handlers(dp)
    setup_channel_handlers(dp)
    setup_content_handlers(dp)

    dp.message.register(start_command, Command("start"))
    dp.message.register(add_channel, Command("add_channel"))  # Nuovo handler per aggiungere canali

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")

from admin_handlers import setup as setup_admin_handlers
setup_admin_handlers(dp)
