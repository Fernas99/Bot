from aiogram import F, Router, types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from bot_setup import bot
from database_manager import DatabaseManager
from states import UserStates
import random

router = Router()
db = DatabaseManager('bot_database.db')


async def show_content_menu(callback_query: types.CallbackQuery, content_type):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Ricerca A-Z", callback_data=f'search_az_{content_type}')],
        [InlineKeyboardButton(text="🎲 Ricerca casuale", callback_data=f'search_random_{content_type}')],
        [InlineKeyboardButton(text="🔍 Ricerca dettagliata", callback_data=f'search_detailed_{content_type}')],
        [InlineKeyboardButton(text="🏷️ Ricerca per genere", callback_data=f'search_genre_{content_type}')],
        [InlineKeyboardButton(text="🔙 Torna al menu principale", callback_data='back_to_main')]
    ])
    await callback_query.message.edit_text(f"Scegli come cercare {content_type}:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('search_'))
async def process_search_selection(callback_query: types.CallbackQuery):
    search_type, content_type = callback_query.data.split('_')[1:]
    if search_type == 'az':
        await show_az_search(callback_query, content_type)
    elif search_type == 'random':
        await show_random_content(callback_query, content_type)
    elif search_type == 'detailed':
        await start_detailed_search(callback_query, content_type)
    elif search_type == 'genre':
        await show_genre_search(callback_query, content_type)


async def show_az_search(callback_query: types.CallbackQuery, content_type):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=letter, callback_data=f'az_{content_type}_{letter}') for letter in letters[i:i + 4]]
        for i in range(0, len(letters), 4)
    ])
    keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_{content_type}'))
    await callback_query.message.edit_text(f"Scegli la lettera iniziale per {content_type}:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('az_'))
async def show_content_by_letter(callback_query: types.CallbackQuery):
    _, content_type, letter = callback_query.data.split('_')
    contents = db.get_contents_by_letter(content_type, letter)
    if contents:
        text = f"Contenuti {content_type} che iniziano per {letter}:\n\n"
        for content in contents:
            text += f"• {content[2]}\n"
    else:
        text = f"Nessun contenuto {content_type} trovato che inizia per {letter}."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_az_{content_type}')]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


async def show_random_content(callback_query: types.CallbackQuery, content_type):
    content = db.get_random_content(content_type)
    if content:
        text = f"Contenuto casuale ({content_type}):\n\n"
        text += f"Titolo: {content[2]}\n"
        text += f"Genere: {content[5]}\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Scarica", callback_data=f'download_{content[0]}')],
            [InlineKeyboardButton(text="🎲 Altro casuale", callback_data=f'search_random_{content_type}')],
            [InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_{content_type}')]
        ])
    else:
        text = f"Nessun contenuto {content_type} disponibile."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_{content_type}')]
        ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


async def start_detailed_search(callback_query: types.CallbackQuery, content_type):
    await callback_query.message.edit_text(
        f"Inserisci il titolo o parte del titolo del {content_type} che stai cercando:")
    await UserStates.WAITING_FOR_SEARCH_QUERY.set()


@router.message(UserStates.WAITING_FOR_SEARCH_QUERY)
async def process_detailed_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    contents = db.search_contents(query)
    if contents:
        text = "Risultati della ricerca:\n\n"
        for content in contents:
            text += f"• {content[2]} ({content[4]})\n"
    else:
        text = "Nessun risultato trovato."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='search_menu')]
    ])
    await message.reply(text, reply_markup=keyboard)
    await state.clear()


async def show_genre_search(callback_query: types.CallbackQuery, content_type):
    genres = db.get_genres(content_type)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=genre, callback_data=f'genre_{content_type}_{genre}')]
        for genre in genres
    ])
    keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_{content_type}'))
    await callback_query.message.edit_text(f"Scegli un genere per {content_type}:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('genre_'))
async def show_content_by_genre(callback_query: types.CallbackQuery):
    _, content_type, genre = callback_query.data.split('_')
    contents = db.get_contents_by_genre(content_type, genre)
    if contents:
        text = f"Contenuti {content_type} del genere {genre}:\n\n"
        for content in contents:
            text += f"• {content[2]}\n"
    else:
        text = f"Nessun contenuto {content_type} trovato per il genere {genre}."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_genre_{content_type}')]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('download_'))
async def download_content(callback_query: types.CallbackQuery):
    content_id = int(callback_query.data.split('_')[1])
    content = db.get_content_by_id(content_id)
    if content:
        file_id = content[1]
        await bot.send_document(callback_query.from_user.id, file_id, caption=f"Ecco il tuo file: {content[2]}")
        db.increment_download_count(content_id)
        await callback_query.answer("Download avviato!")
    else:
        await callback_query.answer("Contenuto non trovato.")


def setup(dp: Dispatcher):
    dp.include_router(router)
