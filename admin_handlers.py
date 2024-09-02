import logging
import asyncio
from aiogram import F, Router, types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from bot_setup import bot
from database_manager import DatabaseManager
from states import AdminStates
from config import ADMIN_IDS

router = Router()
db = DatabaseManager('bot_database.db')


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


async def show_admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per accedere al menu admin.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Gestisci Canali", callback_data='manage_channels')],
        [InlineKeyboardButton(text="Gestisci Contenuti", callback_data='manage_content')],
        [InlineKeyboardButton(text="Gestisci Admin", callback_data='manage_admins')],
        [InlineKeyboardButton(text="Impostazioni", callback_data='settings')],
        [InlineKeyboardButton(text="Messaggio globale", callback_data='global_message')],
        [InlineKeyboardButton(text="Info", callback_data='show_info')]
    ])
    await message.answer('Menu Admin:', reply_markup=keyboard)


@router.callback_query(F.data == 'manage_channels')
async def manage_channels(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Aggiungi Canale", callback_data='add_channel')],
        [InlineKeyboardButton(text="Rimuovi Canale", callback_data='remove_channel')],
        [InlineKeyboardButton(text="Lista Canali", callback_data='list_channels')],
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='admin_menu')]
    ])
    await callback_query.message.edit_text("Gestione Canali:", reply_markup=keyboard)


@router.callback_query(F.data == 'add_channel')
async def add_channel(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    await callback_query.message.edit_text("Invia il link del canale da aggiungere:")
    await state.set_state(AdminStates.WAITING_FOR_CHANNEL_LINK)


@router.message(AdminStates.WAITING_FOR_CHANNEL_LINK)
async def process_channel_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per questa azione.")
        return

    channel_link = message.text
    # Qui dovresti aggiungere la logica per validare e aggiungere il canale
    # Per esempio: db.add_channel(channel_link)
    await message.reply(f"Canale {channel_link} aggiunto con successo!")
    await state.clear()
    await show_admin_menu(message)


@router.callback_query(F.data == 'manage_content')
async def manage_content(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Aggiungi Contenuto", callback_data='add_content')],
        [InlineKeyboardButton(text="Rimuovi Contenuto", callback_data='remove_content')],
        [InlineKeyboardButton(text="Lista Contenuti", callback_data='list_content')],
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='admin_menu')]
    ])
    await callback_query.message.edit_text("Gestione Contenuti:", reply_markup=keyboard)


@router.callback_query(F.data == 'add_content')
async def add_content(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    await callback_query.message.edit_text("Invia il file del contenuto da aggiungere:")
    await state.set_state(AdminStates.WAITING_FOR_FILE)


@router.message(AdminStates.WAITING_FOR_FILE, F.document | F.video)
async def process_content_file(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per questa azione.")
        return

    file_id = message.document.file_id if message.document else message.video.file_id
    file_name = message.document.file_name if message.document else message.video.file_name
    await state.update_data(file_id=file_id, file_name=file_name)
    await message.reply("File ricevuto. Ora inserisci il titolo del contenuto:")
    await state.set_state(AdminStates.WAITING_FOR_TITLE)


@router.message(AdminStates.WAITING_FOR_TITLE)
async def process_content_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per questa azione.")
        return

    title = message.text
    await state.update_data(title=title)
    await message.reply("Titolo registrato. Seleziona il tipo di contenuto:",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Film", callback_data="content_type_film")],
                            [InlineKeyboardButton(text="Serie TV", callback_data="content_type_serie")]
                        ]))
    await state.set_state(AdminStates.WAITING_FOR_CONTENT_TYPE)


@router.callback_query(F.data.startswith('content_type_'))
async def process_content_type(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    content_type = callback_query.data.split('_')[-1]
    await state.update_data(content_type=content_type)
    await callback_query.message.edit_text("Tipo di contenuto registrato. Ora inserisci il genere:")
    await state.set_state(AdminStates.WAITING_FOR_GENRE)


@router.message(AdminStates.WAITING_FOR_GENRE)
async def process_genre(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per questa azione.")
        return

    genre = message.text
    data = await state.get_data()

    # Salva il contenuto nel database
    db.add_content(data['file_id'], data['title'], data['file_name'], data['content_type'], genre)

    await message.reply(f"Contenuto aggiunto con successo!\n"
                        f"Titolo: {data['title']}\n"
                        f"Tipo: {data['content_type']}\n"
                        f"Genere: {genre}")
    await state.clear()
    await show_admin_menu(message)


@router.callback_query(F.data == 'remove_content')
async def remove_content(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    contents = db.get_all_contents()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=content[2], callback_data=f'remove_{content[0]}')]
        for content in contents
    ])
    keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data='manage_content'))
    await callback_query.message.edit_text("Seleziona il contenuto da rimuovere:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('remove_'))
async def confirm_remove_content(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    content_id = int(callback_query.data.split('_')[1])
    content = db.get_content_by_id(content_id)
    if content:
        db.remove_content(content_id)
        await callback_query.answer(f"Contenuto '{content[2]}' rimosso con successo.")
    else:
        await callback_query.answer("Contenuto non trovato.")
    await manage_content(callback_query)


@router.callback_query(F.data == 'list_content')
async def list_content(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    contents = db.get_all_contents()
    content_list = "\n".join([f"{content[2]} - {content[4]} - {content[5]}" for content in contents])
    await callback_query.message.edit_text(f"Lista dei contenuti:\n\n{content_list}")


@router.callback_query(F.data == 'global_message')
async def start_global_message(callback_query: CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    await callback_query.message.edit_text("Inserisci il messaggio globale da inviare a tutti gli utenti:")
    await state.set_state(AdminStates.WAITING_FOR_GLOBAL_MESSAGE)


@router.message(AdminStates.WAITING_FOR_GLOBAL_MESSAGE)
async def send_global_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Non hai i permessi per questa azione.")
        return

    global_message = message.text
    users = db.get_all_users()
    for user_id in users:
        try:
            await bot.send_message(user_id, global_message)
            await asyncio.sleep(0.05)  # Per evitare di superare i limiti di invio
        except Exception as e:
            print(f"Errore nell'invio del messaggio all'utente {user_id}: {e}")

    await message.reply("Messaggio globale inviato con successo.")
    await state.clear()
    await show_admin_menu(message)


@router.callback_query(F.data == 'show_info')
async def show_info(callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Non hai i permessi per questa azione.")
        return

    total_users = db.get_total_users()
    total_contents = db.get_total_contents()
    total_downloads = db.get_total_downloads()

    info_text = f"Statistiche del bot:\n\n" \
                f"Utenti totali: {total_users}\n" \
                f"Contenuti totali: {total_contents}\n" \
                f"Download totali: {total_downloads}"

    await callback_query.message.edit_text(info_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='admin_menu')]
    ]))


@router.callback_query(F.data == 'admin_menu')
async def back_to_admin_menu(callback_query: CallbackQuery):
    await show_admin_menu(callback_query.message)


def setup(dp: Dispatcher):
    dp.include_router(router)
