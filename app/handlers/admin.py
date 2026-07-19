from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from app.config import settings
from app.database import stats,grant,revoke,get_user
router=Router()
def admin(m): return m.from_user and m.from_user.id==settings.admin_id

@router.message(Command('admin'))
@router.message(F.text=='🛠 Админ-панель')
async def panel(m:Message):
    if not admin(m): return
    s=stats(); await m.answer(f"🛠 <b>Админ-панель</b>\n\n👥 Пользователей: {s['total']}\n🆕 Новых сегодня: {s['new']}\n🟢 Активны за 5 минут: {s['active']}\n💎 Premium: {s['premium']}\n💬 Запросов сегодня: {s['req']}\n❌ Ошибок: {s['err']}\n\n/grant ID\n/revoke ID\n/user ID",parse_mode='HTML')

@router.message(Command('grant'))
async def do_grant(m:Message):
    if not admin(m): return
    p=(m.text or '').split()
    if len(p)!=2 or not p[1].isdigit(): return await m.answer('Пример: /grant 123456789')
    await m.answer('✅ Бессрочный Premium выдан.' if grant(int(p[1])) else 'Пользователь не найден. Он должен нажать /start.')

@router.message(Command('revoke'))
async def do_revoke(m:Message):
    if not admin(m): return
    p=(m.text or '').split()
    if len(p)!=2 or not p[1].isdigit(): return await m.answer('Пример: /revoke 123456789')
    await m.answer('Доступ возвращён на Free.' if revoke(int(p[1])) else 'Пользователь не найден.')

@router.message(Command('user'))
async def user(m:Message):
    if not admin(m): return
    p=(m.text or '').split()
    if len(p)!=2 or not p[1].isdigit(): return await m.answer('Пример: /user 123456789')
    u=get_user(int(p[1])); await m.answer('Пользователь не найден.' if not u else f"ID: {u['telegram_id']}\nИмя: {u['first_name']}\n@{u['username'] or 'нет'}\nДоступ: {u['access_type']}\nАктивность: {u['last_activity']}")
