import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TOKEN, DB_NAME
import queries

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_task_id = State()


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(queries.CREATE_USERS_TABLE)
        cursor.execute(queries.CREATE_TASKS_TABLE)
        conn.commit()

def db_execute(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def db_fetch(query, params=(), fetchall=True):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall() if fetchall else cursor.fetchone()


def get_main_menu():
    kb = [
        [KeyboardButton(text="/tasks"), KeyboardButton(text="/add")],
        [KeyboardButton(text="/done"), KeyboardButton(text="/stats")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message):
    db_execute(queries.REGISTER_USER, (message.from_user.id, message.from_user.username, message.from_user.first_name))
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я бот для управления задачами.",
        reply_markup=get_main_menu()
    )

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await message.answer("Введите название новой задачи:")
    await state.set_state(TaskStates.waiting_for_title)

@router.message(TaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    if not message.text or message.text.startswith("/"):
        await message.answer("Название задачи не может быть пустым или командой. Попробуйте еще раз.")
        return
    db_execute(queries.ADD_TASK, (message.from_user.id, message.text))
    await message.answer(f"Задача «{message.text}» добавлена!", reply_markup=get_main_menu())
    await state.clear()

@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    tasks = db_fetch(queries.GET_USER_TASKS, (message.from_user.id,))
    if not tasks:
        await message.answer("У вас пока нет задач.")
        return
    
    response = "📋 Ваши задачи:\n\n"
    for idx, task in enumerate(tasks, 1):
        task_id, title, is_done = task
        status = "✅ выполнена" if is_done == 1 else "⬜ не выполнена"
        response += f"{idx}. {title} (ID: {task_id}) — {status}\n"
    await message.answer(response)

@router.message(Command("done"))
async def cmd_done(message: Message, state: FSMContext):
    await message.answer("Введите ID задачи, чтобы отметить её выполненной:")
    await state.set_state(TaskStates.waiting_for_task_id)

@router.message(TaskStates.waiting_for_task_id)
async def process_task_done(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ошибка! Введите числовой ID задачи.")
        return
        
    task_id = int(message.text)
    task = db_fetch(queries.GET_TASK_BY_ID, (task_id,), fetchall=False)
    
    if not task:
        await message.answer("Ошибка! Задача с таким ID не найдена.")
        await state.clear()
        return
        
    owner_id, is_done = task
    if owner_id != message.from_user.id:
        await message.answer("Ошибка! Это не ваша задача.")
        await state.clear()
        return
        
    if is_done == 1:
        await message.answer("Задача уже выполнена.")
        await state.clear()
        return
        
    db_execute(queries.MARK_TASK_DONE, (task_id,))
    await message.answer(f"Задача ID {task_id} выполнена!", reply_markup=get_main_menu())
    await state.clear()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = db_fetch(queries.GET_STATS, (message.from_user.id,), fetchall=False)
    if not stats:
        await message.answer("У вас нет задач. Всего задач: 0")
        return
        
    total, done, not_done = stats
    await message.answer(
        f"📊 Статистика:\n"
        f"Всего задач: {total}\n"
        f"Выполнено: {done if done else 0}\n"
        f"Не выполнено: {not_done if not_done else 0}"
    )

async def main():
    init_db()
    dp.include_router(router)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
