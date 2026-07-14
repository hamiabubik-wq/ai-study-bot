from aiogram.fsm.state import State, StatesGroup


class StudyForm(StatesGroup):
    choosing_class = State()
    entering_name = State()
    choosing_subject = State()
    choosing_input_type = State()
    waiting_for_text = State()
    waiting_for_image = State()
