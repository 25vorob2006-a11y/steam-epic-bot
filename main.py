import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading

# --- Конфигурация ---
BOT_TOKEN = "8235703111:AAEFJajikE-Dxjy_KFAfTyJDgWWjXevz8h4"
CHECK_INTERVAL_STEAM = 1800  # 30 минут
CHECK_INTERVAL_EPIC = 3600   # 1 час

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Flask сервер для Render ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is running 🚀"

def start_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
    print(f"✅ User {user_id} added")

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

# --- Клавиатуры ---
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Текущие скидки"), KeyboardButton(text="🔥 Steam скидки")],
            [KeyboardButton(text="🎁 Бесплатные Epic"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_deals_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_deals")],
            [InlineKeyboardButton(text="📊 Все скидки Steam", callback_data="all_steam")],
            [InlineKeyboardButton(text="🎯 Все бесплатные Epic", callback_data="all_epic")]
        ]
    )
    return keyboard

# --- Парсеры (заглушки) ---
def get_steam_deals():
    return [
        {
            "id": "1", 
            "title": "Example Steam Game", 
            "original_price": "$29.99", 
            "final_price": "$14.99", 
            "discount": "50", 
            "url": "https://store.steampowered.com/app/123"
        }
    ]

def get_epic_free_games():
    return [
        {
            "id": "1", 
            "title": "Free Epic Game", 
            "url": "https://store.epicgames.com/free-game-1"
        }
    ]

# --- Функции отправки скидок ---
async def send_current_deals(user_id):
    try:
        steam_deals = get_steam_deals()
        epic_deals = get_epic_free_games()
        
        if steam_deals:
            await bot.send_message(user_id, "🔥 **Текущие скидки Steam:**", reply_markup=get_deals_keyboard())
            for deal in steam_deals:
                text = f"🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                await bot.send_message(user_id, text)
        
        if epic_deals:
            await bot.send_message(user_id, "🎁 **Бесплатные игры Epic:**", reply_markup=get_deals_keyboard())
            for deal in epic_deals:
                text = f"🎮 {deal['title']}\n🔗 {deal['url']}"
                await bot.send_message(user_id, text)
                
    except Exception as e:
        print(f"Error: {e}")

# --- Хэндлеры ---
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    
    welcome_text = """
🎮 **Добро пожаловать в Steam & Epic Deals Bot!**

Я присылаю:
• 🔥 Скидки из Steam
• 🎁 Бесплатные игры из Epic Games
    """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    await message.answer("Загружаю текущие скидки...")
    await send_current_deals(user_id)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 **Команды бота:**
/start - начать работу
/help - справка

🎮 **Кнопки:**
Текущие скидки - все акции
Steam скидки - только Steam
Бесплатные Epic - только Epic
Помощь - эта справка
    """
    await message.answer(help_text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "🎮 Текущие скидки")
async def current_deals_handler(message: types.Message):
    await message.answer("Загружаю скидки...")
    await send_current_deals(message.from_user.id)

@dp.message(lambda message: message.text == "🔥 Steam скидки")
async def steam_deals_handler(message: types.Message):
    try:
        steam_deals = get_steam_deals()
        if steam_deals:
            await message.answer("🔥 **Скидки Steam:**")
            for deal in steam_deals:
                text = f"🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                await message.answer(text)
    except Exception as e:
        await message.answer("Ошибка при загрузке скидок Steam")

@dp.message(lambda message: message.text == "🎁 Бесплатные Epic")
async def epic_deals_handler(message: types.Message):
    try:
        epic_deals = get_epic_free_games()
        if epic_deals:
            await message.answer("🎁 **Бесплатные игры Epic:**")
            for deal in epic_deals:
                text = f"🎮 {deal['title']}\n🔗 {deal['url']}"
                await message.answer(text)
    except Exception as e:
        await message.answer("Ошибка при загрузке игр Epic")

@dp.message(lambda message: message.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await help_command(message)

# --- Инлайн-кнопки ---
@dp.callback_query(lambda callback: callback.data == "refresh_deals")
async def refresh_deals(callback: types.CallbackQuery):
    await callback.answer("Обновляю...")
    await callback.message.answer("🔄 Обновляю скидки...")
    await send_current_deals(callback.from_user.id)

# --- Фоновая рассылка ---
async def send_deals():
    while True:
        try:
            users = get_users()
            print(f"📢 Рассылка для {len(users)} пользователей")
            
            steam_deals = get_steam_deals()
            for deal in steam_deals:
                if is_new_deal("steam_" + deal["id"]):
                    for user in users:
                        text = f"🔥 Новая скидка Steam!\n🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("steam_" + deal["id"])
            
            epic_deals = get_epic_free_games()
            for deal in epic_deals:
                if is_new_deal("epic_" + deal["id"]):
                    for user in users:
                        text = f"🎁 Новая бесплатная игра Epic!\n🎮 {deal['title']}\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("epic_" + deal["id"])
        
        except Exception as e:
            print(f"Error in send_deals: {e}")
        
        await asyncio.sleep(min(CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC))

# --- Основная функция ---
async def main():
    print("🚀 Starting Telegram Bot...")
    init_db()
    
    # Удаляем вебхук если был
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем Flask сервер в отдельном потоке
    threading.Thread(target=start_server, daemon=True).start()
    
    # Запускаем рассылку в фоне
    asyncio.create_task(send_deals())
    
    # Запускаем polling
    print("🤖 Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())