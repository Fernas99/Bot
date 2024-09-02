from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from states import UserStates  # Cambiato da BotStates a UserStates
from database_manager import DatabaseManager

router = Router()
db = DatabaseManager('bot_database.db')

@router.callback_query(F.data == 'manage_channels')
async def manage_channels(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Aggiungi Canale", callback_data='add_channel')],
        [InlineKeyboardButton(text="Rimuovi Canale", callback_data='remove_channel')],
        [InlineKeyboardButton(text="Lista Canali", callback_data='list_channels')],
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='admin_menu')]
    ])
    await callback_query.message.edit_text("Gestione Canali:", reply_markup=keyboard)

@router.callback_query(F.data == 'add_channel')
async def add_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Invia il link del canale da aggiungere:")
    await state.set_state(BotStates.WAITING_FOR_CHANNEL_LINK)

@router.callback_query(F.data == 'remove_channel')
async def remove_channel(callback_query: types.CallbackQuery):
    if not CHANNELS:
        await callback_query.answer("Non ci sono canali da rimuovere.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=channel, callback_data=f'remove_channel_{channel_id}')]
        for channel_id, channel in CHANNELS.items()
    ])
    keyboard.add(InlineKeyboardButton(text="🔙 Indietro", callback_data='manage_channels'))
    await callback_query.message.edit_text("Seleziona il canale da rimuovere:", reply_markup=keyboard)

@router.callback_query(F.data == 'list_channels')
async def list_channels(callback_query: types.CallbackQuery):
    if not CHANNELS:
        channels_list = "Nessun canale presente."
    else:
        channels_list = "\n".join([f"{channel}" for channel in CHANNELS.values()])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Indietro", callback_data='manage_channels')]
    ])
    await callback_query.message.edit_text(f"Lista dei canali:\n\n{channels_list}", reply_markup=keyboard)

@router.callback_query(F.data.startswith('remove_channel_'))
async def confirm_remove_channel(callback_query: types.CallbackQuery):
    channel_id = callback_query.data.split('_')[-1]
    channel_name = CHANNELS.get(channel_id, "Canale sconosciuto")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Sì, rimuovi", callback_data=f'confirm_remove_{channel_id}')],
        [InlineKeyboardButton(text="No, annulla", callback_data='manage_channels')]
    ])
    await callback_query.message.edit_text(f"Sei sicuro di voler rimuovere il canale {channel_name}?",
                                           reply_markup=keyboard)

@router.callback_query(F.data.startswith('confirm_remove_'))
async def remove_channel_confirmed(callback_query: types.CallbackQuery):
    channel_id = callback_query.data.split('_')[-1]
    if channel_id in CHANNELS:
        del CHANNELS[channel_id]
        await callback_query.answer("Canale rimosso con successo.")
    else:
        await callback_query.answer("Canale non trovato.")

def setup(dp):
    dp.include_router(router)
