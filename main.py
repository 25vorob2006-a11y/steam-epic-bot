import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "8235703111:AAEFJajikE-Dxjy_KFAfTyJDgWWjXevz8h4")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Нужно установить в переменных окружения Render
WEBHOOK_PATH = "/webhook"
CHECK_INTERVAL_STEAM = 1800
CHECK_INTERVAL_EPIC = 3600

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS deals (deal_id TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"✅ User {user_id} added")

def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [user[0] for user in cursor.fetchall()]
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

# Клавиатуры
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Текущие скидки"), KeyboardButton(text="🔥 Steam скидки")],
            [KeyboardButton(text="🎁 Бесплатные Epic"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def get_deals_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_deals")],
            [InlineKeyboardButton(text="📊 Все скидки Steam", callback_data="all_steam")],
            [InlineKeyboardButton(text="🎯 Все бесплатные Epic", callback_data="all_epic")]
        ]
    )

# Парсеры (заглушки - нужно заменить на реальные)
def get_steam_deals():
    """Заглушка для парсера Steam скидок"""
    return [{
        "id": "1", 
        "title": "Example Steam Game", 
        "original_price": "$29.99", 
        "final_price": "$14.99", 
        "discount": "50", 
        "url": "https://store.steampowered.com/app/123"
    }]

def get_epic_free_games():
    """Заглушка для парсера Epic Games"""
    return [{
        "id": "1", 
        "title": "Free Epic Game", 
        "url": "https://store.epicgames.com/free-game-1"
    }]

# Функции отправки скидок
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
                
        if not steam_deals and not epic_deals:
            await bot.send_message(user_id, "❌ На данный момент нет доступных скидок или бесплатных игр.")
            
    except Exception as e:
        logger.error(f"Error sending deals: {e}")
        await bot.send_message(user_id, "❌ Произошла ошибка при загрузке скидок.")

# Хэндлеры
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    
    await message.answer(
        "🎮 **Добро пожаловать в Steam & Epic Deals Bot!**\n\nЯ присылаю скидки из Steam и бесплатные игры из Epic Games.",
        reply_markup=get_main_keyboard()
    )
    await message.answer("Загружаю текущие скидки...")
    await send_current_deals(user_id)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 **Команды бота:**
/start - начать работу
/help - справка
/deals - текущие скидки

🎮 **Кнопки:**
🎮 Текущие скидки - все акции
🔥 Steam скидки - только Steam
🎁 Бесплатные Epic - только Epic
ℹ️ Помощь - эта справка
    """
    await message.answer(help_text, reply_markup=get_main_keyboard())

@dp.message(Command("deals"))
async def deals_command(message: types.Message):
    await message.answer("Загружаю текущие скидки...")
    await send_current_deals(message.from_user.id)

# Обработчики кнопок
@dp.message(lambda message: message.text == "🎮 Текущие скидки")
async def current_deals_handler(message: types.Message):
    await message.answer("Загружаю скидки...")
    await send_current_deals(message.from_user.id)

@dp.message(lambda message: message.text == "🔥 Steam скидки")
async def steam_deals_handler(message: types.Message):
    steam_deals = get_steam_deals()
    if steam_deals:
        await message.answer("🔥 **Скидки Steam:**")
        for deal in steam_deals:
            text = f"🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
            await message.answer(text)
    else:
        await message.answer("❌ На данный момент нет скидок в Steam.")

@dp.message(lambda message: message.text == "🎁 Бесплатные Epic")
async def epic_deals_handler(message: types.Message):
    epic_deals = get_epic_free_games()
    if epic_deals:
        await message.answer("🎁 **Бесплатные игры Epic:**")
        for deal in epic_deals:
            text = f"🎮 {deal['title']}\n🔗 {deal['url']}"
            await message.answer(text)
    else:
        await message.answer("❌ На данный момент нет бесплатных игр в Epic Games.")

@dp.message(lambda message: message.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await help_command(message)

# Инлайн-кнопки
@dp.callback_query(lambda callback: callback.data == "refresh_deals")
async def refresh_deals(callback: types.CallbackQuery):
    await callback.answer("Обновляю...")
    await callback.message.answer("🔄 Обновляю скидки...")
    await send_current_deals(callback.from_user.id)

# Фоновая задача для проверки скидок
async def check_deals_periodically():
    """Фоновая задача для периодической проверки скидок"""
    while True:
        try:
            users = get_users()
            if users:
                logger.info(f"🔍 Проверяю скидки для {len(users)} пользователей")
                
                steam_deals = get_steam_deals()
                for deal in steam_deals:
                    deal_id = f"steam_{deal['id']}"
                    if is_new_deal(deal_id):
                        logger.info(f"🔥 Новая скидка Steam: {deal['title']}")
                        for user in users:
                            try:
                                text = f"🔥 Новая скидка Steam!\n🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                                await bot.send_message(user, text)
                            except Exception as e:
                                logger.error(f"Error sending to user {user}: {e}")
                        save_deal(deal_id)
                
                epic_deals = get_epic_free_games()
                for deal in epic_deals:
                    deal_id = f"epic_{deal['id']}"
                    if is_new_deal(deal_id):
                        logger.info(f"🎁 Новая бесплатная игра Epic: {deal['title']}")
                        for user in users:
                            try:
                                text = f"🎁 Новая бесплатная игра Epic!\n🎮 {deal['title']}\n🔗 {deal['url']}"
                                await bot.send_message(user, text)
                            except Exception as e:
                                logger.error(f"Error sending to user {user}: {e}")
                        save_deal(deal_id)
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(min(CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC))
            
        except Exception as e:
            logger.error(f"Error in background task: {e}")
            await asyncio.sleep(60)  # Ждем минуту при ошибке

# Веб-сервер для Render
async def on_startup(app):
    """Действия при запуске бота"""
    logger.info("🚀 Starting Telegram Bot...")
    init_db()
    
    # Устанавливаем вебхук если указан URL
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
    else:
        # Если нет WEBHOOK_URL, используем polling (для разработки)
        logger.warning("⚠️ WEBHOOK_URL not set, using polling mode")
    
    # Запускаем фоновую задачу
    asyncio.create_task(check_deals_periodically())

async def on_shutdown(app):
    """Действия при остановке бота"""
    logger.info("🛑 Shutting down bot...")
    await bot.session.close()

# Создаем веб-приложение
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Настраиваем обработчик вебхуков
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
    secret_token="YOUR_SECRET_TOKEN"  # Можно установить в переменных окружения
)
webhook_requests_handler.register(app, path=WEBHOOK_PATH)

# Запуск приложения
if __name__ == "__main__":
    # Если нет WEBHOOK_URL, запускаем в режиме polling
    if not WEBHOOK_URL:
        logger.info("🤖 Starting in polling mode...")
        async def start_polling():
            init_db()
            asyncio.create_task(check_deals_periodically())
            await dp.start_polling(bot)
        
        asyncio.run(start_polling())
    else:
        # Запускаем веб-сервер для Render
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))