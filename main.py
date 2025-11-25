import asyncio
import os
from fastapi import FastAPI
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC
from steam_parser import get_steam_deals
from epic_parser import get_epic_free_games
from database import add_user, get_users, save_deal, is_new_deal

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Создаем клавиатуры
def get_main_keyboard():
    """Основная клавиатура меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Текущие скидки"), KeyboardButton(text="🔥 Steam скидки")],
            [KeyboardButton(text="🎁 Бесплатные Epic"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

def get_deals_keyboard():
    """Инлайн-кнопки для скидок"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_deals")],
            [InlineKeyboardButton(text="📊 Все скидки Steam", callback_data="all_steam"),
             InlineKeyboardButton(text="🎯 Все бесплатные Epic", callback_data="all_epic")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
        ]
    )
    return keyboard

def get_back_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
        ]
    )
    return keyboard

# Функция для отправки текущих скидок пользователю
async def send_current_deals(user_id, show_keyboard=True):
    try:
        # Получаем текущие скидки Steam
        steam_deals = get_steam_deals()
        epic_deals = get_epic_free_games()
        
        if not steam_deals and not epic_deals:
            await bot.send_message(user_id, "На данный момент нет актуальных скидок.")
            return

        keyboard = get_deals_keyboard() if show_keyboard else None
        
        if steam_deals:
            await bot.send_message(user_id, "🔥 **Текущие горячие скидки Steam:**", reply_markup=keyboard)
            for deal in steam_deals[:3]:  # Первые 3 скидки
                text = f"🎮 *{deal['title']}*\n💰 {deal['original_price']} → *{deal['final_price']}* ({deal['discount']}%)\n🔗 [Ссылка на игру]({deal['url']})"
                await bot.send_message(user_id, text, parse_mode='Markdown')
        
        if epic_deals:
            await bot.send_message(user_id, "🎁 **Текущие бесплатные игры Epic Games:**", reply_markup=keyboard)
            for deal in epic_deals[:3]:  # Первые 3 игры
                text = f"🎮 *{deal['title']}*\n🔗 [Получить бесплатно]({deal['url']})"
                await bot.send_message(user_id, text, parse_mode='Markdown')
                
    except Exception as e:
        print(f"Error sending current deals: {e}")
        await bot.send_message(user_id, "Произошла ошибка при получении скидок.")

# Функция для отправки всех скидок Steam
async def send_all_steam_deals(user_id):
    try:
        steam_deals = get_steam_deals()
        if not steam_deals:
            await bot.send_message(user_id, "На данный момент нет скидок в Steam.")
            return
            
        await bot.send_message(user_id, f"🔥 **Все текущие скидки Steam ({len(steam_deals)}):**", reply_markup=get_back_keyboard())
        for deal in steam_deals:
            text = f"🎮 *{deal['title']}*\n💰 {deal['original_price']} → *{deal['final_price']}* ({deal['discount']}%)\n🔗 [Ссылка на игру]({deal['url']})"
            await bot.send_message(user_id, text, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Error sending all steam deals: {e}")

# Функция для отправки всех бесплатных игр Epic
async def send_all_epic_deals(user_id):
    try:
        epic_deals = get_epic_free_games()
        if not epic_deals:
            await bot.send_message(user_id, "На данный момент нет бесплатных игр в Epic Games.")
            return
            
        await bot.send_message(user_id, f"🎁 **Все бесплатные игры Epic ({len(epic_deals)}):**", reply_markup=get_back_keyboard())
        for deal in epic_deals:
            text = f"🎮 *{deal['title']}*\n🔗 [Получить бесплатно]({deal['url']})"
            await bot.send_message(user_id, text, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Error sending all epic deals: {e}")

# Хэндлеры команд
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    
    welcome_text = """
🎮 **Добро пожаловать в Steam & Epic Deals Bot!**

Я буду присылать вам:
• 🔥 Горячие скидки из Steam
• 🎁 Бесплатные игры из Epic Games

Выберите действие в меню ниже 👇
    """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    await asyncio.sleep(1)
    await message.answer("Загружаю текущие скидки...")
    await send_current_deals(user_id)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 **Команды бота:**

*Основные команды:*
/start - начать работу
/help - показать справку
/deals - получить текущие скидки

*Быстрые кнопки:*
🎮 Текущие скидки - все актуальные предложения
🔥 Steam скидки - только скидки Steam
🎁 Бесплатные Epic - только бесплатные игры Epic
ℹ️ Помощь - это сообщение

Бот автоматически присылает новые скидки!
    """
    await message.answer(help_text, reply_markup=get_main_keyboard())

@dp.message(Command("deals"))
async def deals_command(message: types.Message):
    """Ручной запрос текущих скидок"""
    await message.answer("Загружаю текущие скидки...", reply_markup=get_main_keyboard())
    await send_current_deals(message.from_user.id)

# Обработчики текстовых сообщений (кнопки меню)
@dp.message(lambda message: message.text == "🎮 Текущие скидки")
async def current_deals_handler(message: types.Message):
    await message.answer("Загружаю все актуальные скидки...")
    await send_current_deals(message.from_user.id)

@dp.message(lambda message: message.text == "🔥 Steam скидки")
async def steam_deals_handler(message: types.Message):
    await message.answer("Загружаю скидки Steam...")
    await send_all_steam_deals(message.from_user.id)

@dp.message(lambda message: message.text == "🎁 Бесплатные Epic")
async def epic_deals_handler(message: types.Message):
    await message.answer("Загружаю бесплатные игры Epic...")
    await send_all_epic_deals(message.from_user.id)

@dp.message(lambda message: message.text == "ℹ️ Помощь")
async def help_handler(message: types.Message):
    await help_command(message)

# Обработчики инлайн-кнопок
@dp.callback_query(lambda callback: callback.data == "refresh_deals")
async def refresh_deals(callback: types.CallbackQuery):
    await callback.answer("Обновляю скидки...")
    await callback.message.answer("🔄 Загружаю обновленные скидки...")
    await send_current_deals(callback.from_user.id, show_keyboard=False)

@dp.callback_query(lambda callback: callback.data == "all_steam")
async def all_steam_deals(callback: types.CallbackQuery):
    await callback.answer("Загружаю все скидки Steam...")
    await send_all_steam_deals(callback.from_user.id)

@dp.callback_query(lambda callback: callback.data == "all_epic")
async def all_epic_deals(callback: types.CallbackQuery):
    await callback.answer("Загружаю все бесплатные игры Epic...")
    await send_all_epic_deals(callback.from_user.id)

@dp.callback_query(lambda callback: callback.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Возвращаюсь в главное меню:", reply_markup=get_main_keyboard())

@dp.callback_query(lambda callback: callback.data == "settings")
async def settings_handler(callback: types.CallbackQuery):
    await callback.answer("Настройки пока не доступны")

# Функция для автоматической рассылки (фоновая)
async def send_deals():
    while True:
        try:
            users = get_users()
            
            # Steam
            steam_deals = get_steam_deals()
            for deal in steam_deals:
                if is_new_deal("steam_" + deal["id"]):
                    for user in users:
                        text = f"🔥 **Новая скидка Steam!**\n🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("steam_" + deal["id"])
            
            # Epic
            epic_deals = get_epic_free_games()
            for deal in epic_deals:
                if is_new_deal("epic_" + deal["id"]):
                    for user in users:
                        text = f"🎁 **Новая бесплатная игра Epic!**\n🎮 {deal['title']}\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("epic_" + deal["id"])
        
        except Exception as e:
            print(f"Error in send_deals: {e}")
        
        await asyncio.sleep(min(CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC))

# FastAPI роуты
@app.get("/")
def root():
    return {"status": "Bot is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Запуск бота в отдельном потоке чтобы избежать конфликта с FastAPI
async def start_bot():
    print("Starting Telegram bot polling...")
    # Запускаем рассылку в фоне
    asyncio.create_task(send_deals())
    # Запускаем polling
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    # Запускаем только FastAPI для Render
    # Бот будет запускаться только если это не Render
    if not os.environ.get('RENDER'):
        # Локальный запуск с ботом
        async def main():
            await start_bot()
        asyncio.run(main())
    else:
        # На Render запускаем только FastAPI
        print("Running on Render - starting FastAPI only...")
        uvicorn.run(app, host="0.0.0.0", port=port)