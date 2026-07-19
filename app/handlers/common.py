from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.config import settings
from app.database import upsert_user,is_premium,requests_today,history,clear_history
from app.keyboards import main_keyboard
router=Router()

@router.message(Command('start'))
async def start(m:Message,state:FSMContext):
    await state.clear(); upsert_user(m.from_user)
    await m.answer('Привет! Выбери режим:',reply_markup=main_keyboard(m.from_user.id==settings.admin_id))

@router.message(Command('myid'))
async def myid(m:Message): await m.answer(f'Ваш ID: <code>{m.from_user.id}</code>',parse_mode='HTML')

@router.message(F.text=='❌ Отмена')
async def cancel(m:Message,state:FSMContext):
    await state.clear(); await m.answer('Режим закрыт.',reply_markup=main_keyboard(m.from_user.id==settings.admin_id))

@router.message(F.text=='👤 Профиль')
async def profile(m:Message):
    p=is_premium(m.from_user.id); used=requests_today(m.from_user.id)
    await m.answer(f"Статус: {'Premium' if p else 'Free'}\nЗапросы: {'без ограничений' if p else f'{used}/{settings.free_daily_limit}'}\nID: <code>{m.from_user.id}</code>",parse_mode='HTML')

@router.message(F.text=='📜 История')
async def hist(m:Message):
    rows=history(m.from_user.id,limit=10)
    if not rows: return await m.answer('История пустая.')
    text='📜 Последние сообщения:\n'+''.join(f"\n<b>{'Вы' if r['role']=='user' else 'Бот'}:</b> {r['content'][:300]}" for r in rows)+'\n\n/clear_history — очистить'
    await m.answer(text,parse_mode='HTML')

@router.message(Command('clear_history'))
async def clear(m:Message): clear_history(m.from_user.id); await m.answer('История очищена.')
