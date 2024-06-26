import asyncio
import logging
import os
import uuid
from asyncio import sleep

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup, ReplyKeyboardRemove, FSInputFile, CallbackQuery
import config as cnfg

from ObjectStorage import ObjectStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from FaceSimilars import findMostSimilarFace
from Categories import  Categories
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=cnfg.TG_BOT_API)
# Диспетчер
dp = Dispatcher()

# Планировщик
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Определяем состояния
class ActorSearchStates(StatesGroup):
    CHOOSING_TYPE = State()  # Выбор актёра или актрисы
    PHOTO_UPLOAD = State()   # Загрузка фотографии

actorRouter = Router()
textButton = "Узнать схожесть на актёра/актрису по фото"

# Используем requests_queue из предыдущего кода
requests_queue = asyncio.Queue()

semaphore = asyncio.Semaphore(5)  # ограничиваем количество одновременно выполняемых операций

async def consumer():
    while True:
        data, chat_id = await requests_queue.get()
        async with semaphore:
            await answerToUser(data, chat_id)

async def answerToUser(data, chat_id):
    print("lox")
    loop = asyncio.get_running_loop()
    most_similar_photo = await loop.run_in_executor(None, lambda: findMostSimilarFace(data["CHOOSING_TYPE"], data["PHOTO_UPLOAD"]))
    btn = InlineKeyboardButton(text=textButton, callback_data="started")
    row = [btn]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    if most_similar_photo!=None:
        await bot.send_photo(
            chat_id=chat_id, caption=f"Человек на фото похож на {most_similar_photo[1]}",
            photo=FSInputFile(path=most_similar_photo[0]), reply_markup=markup,
        )
        os.remove(most_similar_photo[0])
    else:
        await bot.send_message(chat_id=chat_id, text="На вашем фото лицо не обнаружено(", reply_markup=markup)
    os.remove(data["PHOTO_UPLOAD"])



@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    btn = InlineKeyboardButton(text=textButton, callback_data="started")
    row = [btn]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(
        "Бот успешно запущен!",
        reply_markup=markup,
    )

@actorRouter.callback_query(F.data == "started")
async def startFind(callback_query: CallbackQuery, state: FSMContext)->None:
    await state.set_state(ActorSearchStates.CHOOSING_TYPE)
    #await callback_query.message.delete()
    btn1 = InlineKeyboardButton(text="Актёр", callback_data="actors")
    btn2 = InlineKeyboardButton(text="Актриса", callback_data="actresses")
    btn3 = InlineKeyboardButton(text="XXX", callback_data="XXX")
    row = [btn1, btn2, btn3]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback_query.message.answer(
        "Выберите, кого искать? Актёра или актрису?",
        reply_markup=markup,
    )

@actorRouter.callback_query(ActorSearchStates.CHOOSING_TYPE)
async def uploadPhoto(callback_query: CallbackQuery, state: FSMContext)->None:
    category = None
    if callback_query.data in Categories:
        category = callback_query.data
        print(category)
    else:
        btn1 = InlineKeyboardButton(text="Актёр", callback_data="actors")
        btn2 = InlineKeyboardButton(text="Актриса", callback_data="actresses")
        btn3 = InlineKeyboardButton(text="XXX", callback_data="XXX")
        row = [btn1, btn2, btn3]
        rows = [row]
        markup = InlineKeyboardMarkup(inline_keyboard=rows)
        await callback_query.message.answer("Ошибка! Повторите выбор.", reply_markup=markup,)
    if category is not None:
        await state.update_data(CHOOSING_TYPE=category)
        await state.set_state(ActorSearchStates.PHOTO_UPLOAD)
        await callback_query.message.answer(
            "Загрузите фото человека", reply_markup=ReplyKeyboardRemove()
        )

@actorRouter.message(ActorSearchStates.PHOTO_UPLOAD, F.photo)
async def finish(message: types.Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    unique_filename = str(uuid.uuid4()) + ".jpg"
    downloaded_file = await bot.download_file(file.file_path)
    with open(unique_filename, "wb") as photo:
        photo.write(downloaded_file.read())

    data = await state.update_data(PHOTO_UPLOAD=unique_filename)
    print(data)
    await message.answer("Ожидайте результата, это займёт несколько минут")
    await requests_queue.put((data, message.chat.id))
    await state.clear()

# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(actorRouter)
    asyncio.create_task(consumer())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
