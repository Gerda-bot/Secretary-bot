import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiosqlite
import dateparser
import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

DB_PATH = "secretary.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                priority INTEGER DEFAULT 1,
                due_date TEXT,
                done INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                remind_at TEXT,
                sent INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def reminder_loop():
    while True:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                now = datetime.now().isoformat()
                async with db.execute(
                    "SELECT id, user_id, text FROM reminders WHERE remind_at <= ? AND sent = 0",
                    (now,)
                ) as cursor:
                    rows = await cursor.fetchall()
                for rid, uid, text in rows:
                    try:
                        await bot.send_message(uid, f"⏰ Напоминание: {text}")
                        await db.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (rid,))
                    except Exception as e:
                        logger.error(f"Failed to send reminder {rid}: {e}")
                await db.commit()
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")
        await asyncio.sleep(30)

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я твой личный секретарь-бот.\n\n"
        "Я помогу с задачами, напоминаниями, планированием и поиском информации.\n\n"
        "Напиши /help чтобы увидеть команды."
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 Команды секретаря:\n\n"
        "/addtask <текст> — добавить задачу\n"
        "/tasks — список задач\n"
        "/done <id> — отметить выполненной\n"
        "/remind <время> <текст> — создать напоминание\n"
        "/notes — мои заметки\n"
        "/addnote <текст> — добавить заметку\n"
        "/search <запрос> — поиск в интернете\n"
        "/plan — план на сегодня\n\n"
        "Также можно писать обычным языком:\n"
        "«напомни через 30 минут позвонить»\n"
        "«добавь задачу подготовить презентацию»"
    )

@router.message(Command("addtask"))
async def cmd_addtask(message: Message):
    text = message.text.replace("/addtask", "").strip()
    if not text:
        await message.answer("Напиши текст задачи после команды.")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tasks (user_id, text, created_at) VALUES (?, ?, ?)",
            (message.from_user.id, text, datetime.now().isoformat())
        )
        await db.commit()
    await message.answer(f"✅ Задача добавлена: {text}")

@router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, text, priority, due_date, done FROM tasks WHERE user_id = ? AND done = 0 ORDER BY priority DESC, id",
            (message.from_user.id,)
        ) as cursor:
            rows = await cursor.fetchall()
    if not rows:
        await message.answer("Список задач пуст. Добавьте через /addtask")
        return
    lines = ["📋 Активные задачи:\n"]
    for i, (tid, text, pri, due, done) in enumerate(rows, 1):
        pri_str = "🔴" if pri > 1 else "🟢"
        due_str = f" (до {due[:10]})" if due else ""
        lines.append(f"{i}. {pri_str} {text}{due_str} [id:{tid}]")
    await message.answer("\n".join(lines))

@router.message(Command("done"))
async def cmd_done(message: Message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Укажи номер задачи: /done 1")
        return
    tid = int(parts[1])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
            (tid, message.from_user.id)
        )
        await db.commit()
    await message.answer(f"✅ Задача #{tid} отмечена как выполненная.")

@router.message(Command("remind"))
async def cmd_remind(message: Message):
    text = message.text.replace("/remind", "").strip()
    if not text:
        await message.answer("Пример: /remind через 10 минут позвонить клиенту")
        return
    parsed = dateparser.parse(text, languages=["ru"])
    remind_at = parsed.isoformat() if parsed else (datetime.now() + timedelta(minutes=10)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
            (message.from_user.id, text, remind_at)
        )
        await db.commit()
    await message.answer(f"⏰ Напоминание установлено на {remind_at[:16]}")

@router.message(Command("addnote"))
async def cmd_addnote(message: Message):
    text = message.text.replace("/addnote", "").strip()
    if not text:
        await message.answer("Напиши текст заметки.")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO notes (user_id, text, created_at) VALUES (?, ?, ?)",
            (message.from_user.id, text, datetime.now().isoformat())
        )
        await db.commit()
    await message.answer("📝 Заметка сохранена.")

@router.message(Command("notes"))
async def cmd_notes(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, text, created_at FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (message.from_user.id,)
        ) as cursor:
            rows = await cursor.fetchall()
    if not rows:
        await message.answer("Заметок пока нет.")
        return
    lines = ["📝 Последние заметки:\n"]
    for nid, text, created in rows:
        lines.append(f"• {text[:100]}... ({created[:10]})")
    await message.answer("\n".join(lines))

@router.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("Напиши запрос после /search")
        return
    await message.answer("🔍 Ищу информацию...")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
            )
            data = resp.json()
            abstract = data.get("AbstractText") or data.get("Abstract") or "Ничего не найдено по этому запросу."
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            await message.answer(f"📌 Результат:\n\n{abstract}")
    except Exception as e:
        logger.error(e)
        await message.answer("Не удалось выполнить поиск. Попробуйте позже.")

@router.message(Command("plan"))
async def cmd_plan(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT text FROM tasks WHERE user_id = ? AND done = 0 ORDER BY priority DESC LIMIT 5",
            (message.from_user.id,)
        ) as cursor:
            tasks = await cursor.fetchall()
    if not tasks:
        await message.answer("На сегодня активных задач нет. Отличный день!")
        return
    lines = ["📅 План на сегодня:\n"]
    for i, (text,) in enumerate(tasks, 1):
        lines.append(f"{i}. {text}")
    await message.answer("\n".join(lines))

@router.message(F.text)
async def handle_text(message: Message):
    text = message.text.lower()
    if "напомни" in text or "напомнить" in text:
        parsed = dateparser.parse(message.text, languages=["ru"])
        remind_at = parsed.isoformat() if parsed else (datetime.now() + timedelta(hours=1)).isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
                (message.from_user.id, message.text, remind_at)
            )
            await db.commit()
        await message.answer(f"⏰ Напоминание создано на {remind_at[:16]}")
    elif "добавь задачу" in text or ("задача" in text and "добавь" in text):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO tasks (user_id, text, created_at) VALUES (?, ?, ?)",
                (message.from_user.id, message.text, datetime.now().isoformat())
            )
            await db.commit()
        await message.answer("✅ Задача добавлена.")
    else:
        await message.answer(
            "Я твой секретарь. Используй команды /help или напиши «напомни через час...» "
            "или «добавь задачу...»."
        )

@router.message(F.voice)
async def handle_voice(message: Message):
    await message.answer(
        "🎤 Голосовое сообщение получено. "
        "Для распознавания речи подключите внешний сервис. "
        "Пока используйте текстовые команды."
    )

async def main():
    await init_db()
    dp.include_router(router)
    asyncio.create_task(reminder_loop())
    logger.info("Secretary bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
