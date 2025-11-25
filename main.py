import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from server import start_server
import threading

# --- Конфигурация ---
BOT_TOKEN = "ВАШ_BOT_TOKEN"
CHECK_INTERVAL_STEAM = 1800  # 30 минут
CHECK_INTERVAL_EPIC = 3600   # 1 час

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- База данных ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS deals (deal_id TEXT PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [u[0] for u in cursor.fetchall()]
    conn.close()
    return users

def save_deal(deal_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO deals (deal_id) VALUES (?)', (deal_id,))
    conn.commit()
    conn.close()

def is_new_deal(deal_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM deals WHERE deal_id = ?', (deal_id,))
    exists = cursor.fetchone() is None
    conn.close()
    return exists

# --- Заглушки для парсеров ---
def get_steam_deals():
    return [{"id": "1", "title": "Example Game 1", "original_price": "$29.99", "final_price": "$14.99", "discount": "50", "url": "https://store.steampowered.com/app/123"}]

def get_epic_free_games():
    return [{"id": "1", "title": "Free Epic Game 1", "url": "https://store.epicgames.com/free-game-1"}]

# --- Рассылка ---
async def send_deals():
    while True:
        users = get_users()
        steam_deals = get_steam_deals()
        epic_deals = get_epic_free_games()
        
        for deal in steam_deals:
            if is_new_deal("steam_" + deal["id"]):
                for user in users:
                    await bot.send_message(user, f"🔥 Новая скидка Steam!\n{deal['title']}\n{deal['original_price']} → {deal['final_price']}\n{deal['url']}")
                save_deal("steam_" + deal["id"])
        
        for deal in epic_deals:
            if is_new_deal("epic_" + deal["id"]):
                for user in users:
                    await bot.send_message(user, f"🎁 Новая бесплатная игра Epic!\n{deal['title']}\n{deal['url']}")
                save_deal("epic_" + deal["id"])
        
        await asyncio.sleep(min(CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC))

# --- Команды бота ---
@dp.message(Command("start"))
async def start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer("Привет! Вы подписаны на Steam & Epic deals!")

# --- Основная функция ---
async def main():
    init_db()
    
    # Запускаем веб-сервер в отдельном потоке
    threading.Thread(target=start_server, daemon=True).start()
    
    # Фоновая рассылка
    asyncio.create_task(send_deals())
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
