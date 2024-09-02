from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    WAITING_FOR_SEARCH_QUERY = State()
    WAITING_FOR_SUPPORT_MESSAGE = State()

class AdminStates(StatesGroup):
    WAITING_FOR_CHANNEL_LINK = State()
    WAITING_FOR_FILE = State()
    WAITING_FOR_TITLE = State()
    WAITING_FOR_CONTENT_TYPE = State()
    WAITING_FOR_GENRE = State()
    WAITING_FOR_GLOBAL_MESSAGE = State()
