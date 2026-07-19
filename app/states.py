from aiogram.fsm.state import State, StatesGroup
class BotStates(StatesGroup):
    free_chat = State()
    programmer = State()
    waiting_image = State()
    waiting_document = State()
    voice_chat = State()
    web_search = State()
