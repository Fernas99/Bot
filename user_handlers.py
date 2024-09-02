from aiogram import F, Router, types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from database_manager import DatabaseManager
from states import UserStates
import string

router = Router()
db = DatabaseManager('bot_database.db')

async def show_user_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Film", callback_data='menu_film')],
        [InlineKeyboardButton(text="📺 Serie TV", callback_data='menu_serie')],
        [InlineKeyboardButton(text="🔍 Cerca", callback_data='search')],
        [InlineKeyboardButton(text="ℹ️ Info", callback_data='info')]
    ])
    await message.answer("Benvenuto! Cosa vuoi fare?", reply_markup=keyboard)

@router.callback_query(F.data.startswith('menu_'))
async def show_content_menu(callback_query: CallbackQuery):
    content_type = callback_query.data.split('_')[1]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Ricerca A-Z", callback_data=f'search_az_{content_type}')],
        [InlineKeyboardButton(text="🎲 Ricerca casuale", callback_data=f'search_random_{content_type}')],
        [InlineKeyboardButton(text="🔍 Ricerca dettagliata", callback_data=f'search_detailed_{content_type}')],
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='back_to_main')]
    ])
    await callback_query.message.edit_text(f"Scegli come cercare {content_type}:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('search_az_'))
async def search_az(callback_query: CallbackQuery):
    content_type = callback_query.data.split('_')[2]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=letter, callback_data=f'letter_{content_type}_{letter}') for letter in string.ascii_uppercase[i:i+4]]
        for i in range(0, 26, 4)
    ])
    keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data=f'menu_{content_type}'))
    await callback_query.message.edit_text(f"Scegli la lettera iniziale per {content_type}:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('letter_'))
async def show_content_by_letter(callback_query: CallbackQuery):
    _, content_type, letter = callback_query.data.split('_')
    results = db.get_contents_by_letter(content_type, letter)
    if results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=result[2], callback_data=f'show_content_{result[0]}')]
            for result in results
        ])
        keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data=f'search_az_{content_type}'))
        await callback_query.message.edit_text(f"Risultati per '{letter}':", reply_markup=keyboard)
    else:
        await callback_query.answer(f"Nessun risultato trovato per la lettera '{letter}'")

@router.callback_query(F.data.startswith('search_random_'))
async def search_random(callback_query: CallbackQuery):
    content_type = callback_query.data.split('_')[2]
    random_content = db.get_random_content(content_type)
    if random_content:
        text = f"Titolo: {random_content[2]}\n"
        text += f"Tipo: {random_content[4]}\n"
        text += f"Genere: {random_content[5]}\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Scarica", callback_data=f'download_{random_content[0]}')],
            [InlineKeyboardButton(text="🎲 Altro casuale", callback_data=f'search_random_{content_type}')],
            [InlineKeyboardButton(text="🔙 Indietro", callback_data=f'menu_{content_type}')]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_query.answer(f"Nessun contenuto trovato per {content_type}")

@router.callback_query(F.data.startswith('search_detailed_'))
async def start_detailed_search(callback_query: CallbackQuery, state: FSMContext):
    content_type = callback_query.data.split('_')[2]
    await state.update_data(search_content_type=content_type)
    await callback_query.message.edit_text("Inserisci il titolo o una parte del titolo da cercare:")
    await state.set_state(UserStates.WAITING_FOR_SEARCH_QUERY)

@router.message(UserStates.WAITING_FOR_SEARCH_QUERY)
async def process_search_query(message: Message, state: FSMContext):
    query = message.text.lower()
    data = await state.get_data()
    content_type = data['search_content_type']
    results = db.search_content_detailed(query, content_type)
    if results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=result[2], callback_data=f'show_content_{result[0]}')]
            for result in results
        ])
        keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data=f'menu_{content_type}'))
        await message.reply("Risultati della ricerca:", reply_markup=keyboard)
    else:
        await message.reply("Nessun risultato trovato. Prova con un'altra ricerca.")
    await state.clear()

@router.callback_query(F.data.startswith('show_content_'))
async def show_content_details(callback_query: CallbackQuery):
    content_id = int(callback_query.data.split('_')[2])
    content = db.get_content_by_id(content_id)
    if content:
        text = f"Titolo: {content[2]}\n"
        text += f"Tipo: {content[4]}\n"
        text += f"Genere: {content[5]}\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Scarica", callback_data=f'download_{content_id}')],
            [InlineKeyboardButton(text="🔙 Indietro", callback_data='back_to_main')]
        ])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback_query.answer("Contenuto non trovato.")

@router.callback_query(F.data.startswith('download_'))
async def download_content(callback_query: CallbackQuery):
    content_id = int(callback_query.data.split('_')[1])
    content = db.get_content_by_id(content_id)
    if content:
        file_id = content[1]
        await callback_query.message.answer_document(file_id, caption=f"Ecco il tuo file: {content[2]}")
        db.increment_download_count(content_id)
        await callback_query.answer("Download avviato!")
    else:
        await callback_query.answer("Contenuto non trovato.")

@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback_query: CallbackQuery):
    await show_user_menu(callback_query.message)

@router.callback_query(F.data == 'info')
async def show_info(callback_query: CallbackQuery):
    total_contents = db.get_total_contents()
    total_downloads = db.get_total_downloads()

    info_text = f"Informazioni sul bot:\n\n" \
                f"Contenuti totali: {total_contents}\n" \
                f"Download totali: {total_downloads}"

    await callback_query.message.edit_text(info_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='back_to_main')]
    ]))

def setup(dp: Dispatcher):
    dp.include_router(router)
