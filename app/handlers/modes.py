from io import BytesIO
from aiogram import Bot,F,Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from app.config import settings
from app.database import upsert_user,can_request,log,save_history,history
from app.keyboards import cancel_keyboard,main_keyboard
from app.services.gemini import gemini
from app.services.documents import extract
from app.states import BotStates
router=Router()

async def allowed(m):
    upsert_user(m.from_user)
    if can_request(m.from_user.id): return True
    await m.answer(f'Лимит {settings.free_daily_limit} запросов на сегодня закончился.'); return False
async def send(m,text):
    for i in range(0,len(text),3900): await m.answer(text[i:i+3900])
async def run_text(m,mode,system):
    if not await allowed(m): return
    status=await m.answer('Думаю...')
    try:
        ans=await gemini.text(m.text or '',system,history(m.from_user.id,mode,10)); save_history(m.from_user.id,mode,'user',m.text or ''); save_history(m.from_user.id,mode,'assistant',ans); log(m.from_user.id,mode,True); await send(m,ans)
    except Exception as e: log(m.from_user.id,mode,False); await m.answer(f'Ошибка: {type(e).__name__}')
    finally:
        try: await status.delete()
        except: pass

@router.message(F.text=='💬 Свободный чат')
async def a(m:Message,state:FSMContext): await state.set_state(BotStates.free_chat); await m.answer('Пиши любой вопрос.',reply_markup=cancel_keyboard())
@router.message(BotStates.free_chat,F.text)
async def b(m:Message): await run_text(m,'chat','Ты полезный AI-ассистент. Отвечай по-русски, точно и понятно.')
@router.message(F.text=='💻 Помощник программиста')
async def c(m:Message,state:FSMContext): await state.set_state(BotStates.programmer); await m.answer('Пришли код, ошибку или задачу. Поддерживаются любые языки.',reply_markup=cancel_keyboard())
@router.message(BotStates.programmer,F.text)
async def d(m:Message): await run_text(m,'programmer','Ты опытный помощник программиста по всем языкам. Давай рабочий код и объяснения на русском.')

@router.message(F.text=='🖼 Анализ изображения')
async def e(m:Message,state:FSMContext): await state.set_state(BotStates.waiting_image); await m.answer('Отправь изображение, подпись можно использовать как вопрос.',reply_markup=cancel_keyboard())
@router.message(BotStates.waiting_image,F.photo)
async def f(m:Message,bot:Bot):
    if not await allowed(m): return
    s=await m.answer('Анализирую...')
    try:
        buf=BytesIO(); await bot.download(m.photo[-1],destination=buf); ans=await gemini.bytes(buf.getvalue(),'image/jpeg',m.caption or 'Подробно проанализируй изображение и реши задание, если оно есть.'); log(m.from_user.id,'image',True); save_history(m.from_user.id,'image','assistant',ans); await send(m,ans)
    except Exception as x: log(m.from_user.id,'image',False); await m.answer(f'Ошибка: {type(x).__name__}')
    finally:
        try: await s.delete()
        except: pass

@router.message(F.text=='📄 Анализ документа')
async def g(m:Message,state:FSMContext): await state.set_state(BotStates.waiting_document); await m.answer('Отправь PDF, DOCX, TXT или файл кода.',reply_markup=cancel_keyboard())
@router.message(BotStates.waiting_document,F.document)
async def h(m:Message,bot:Bot):
    if not await allowed(m): return
    s=await m.answer('Читаю документ...')
    try:
        buf=BytesIO(); await bot.download(m.document,destination=buf); text=extract(buf.getvalue(),m.document.file_name or 'file.txt',m.document.mime_type); ans=await gemini.text('Сделай краткое содержание, ключевые мысли и важные ошибки:\n\n'+text,'Ты специалист по анализу документов. Отвечай по-русски.'); log(m.from_user.id,'document',True); save_history(m.from_user.id,'document','assistant',ans); await send(m,ans)
    except Exception as x: log(m.from_user.id,'document',False); await m.answer(f'Ошибка: {x}')
    finally:
        try: await s.delete()
        except: pass

@router.message(F.text=='🎙 Голосовой чат')
async def i(m:Message,state:FSMContext): await state.set_state(BotStates.voice_chat); await m.answer('Отправь голосовое сообщение.',reply_markup=cancel_keyboard())
@router.message(BotStates.voice_chat,F.voice)
async def j(m:Message,bot:Bot):
    if not await allowed(m): return
    s=await m.answer('Слушаю...')
    try:
        buf=BytesIO(); await bot.download(m.voice,destination=buf); ans=await gemini.bytes(buf.getvalue(),m.voice.mime_type or 'audio/ogg','Распознай речь, затем ответь пользователю на русском.'); log(m.from_user.id,'voice',True); save_history(m.from_user.id,'voice','assistant',ans); await send(m,ans)
    except Exception as x: log(m.from_user.id,'voice',False); await m.answer(f'Ошибка: {type(x).__name__}')
    finally:
        try: await s.delete()
        except: pass

@router.message(F.text=='🌐 Поиск в интернете')
async def k(m:Message,state:FSMContext): await state.set_state(BotStates.web_search); await m.answer('Напиши, что найти в интернете.',reply_markup=cancel_keyboard())
@router.message(BotStates.web_search,F.text)
async def l(m:Message):
    if not await allowed(m): return
    s=await m.answer('Ищу...')
    try: ans=await gemini.search(m.text or ''); log(m.from_user.id,'web_search',True); save_history(m.from_user.id,'web','user',m.text or ''); save_history(m.from_user.id,'web','assistant',ans); await send(m,ans)
    except Exception as x: log(m.from_user.id,'web_search',False); await m.answer(f'Ошибка поиска: {type(x).__name__}')
    finally:
        try: await s.delete()
        except: pass

@router.message()
async def fallback(m:Message):
    upsert_user(m.from_user); await m.answer('Выбери режим кнопкой.',reply_markup=main_keyboard(m.from_user.id==settings.admin_id))
