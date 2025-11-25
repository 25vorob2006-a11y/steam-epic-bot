import asyncio
import os
from fastapi import FastAPI
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC
from steam_parser import get_steam_deals
from epic_parser import get_epic_free_games
from database import add_user, get_users, save_deal, is_new_deal

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Функция для отправки текущих скидок пользователю
async def send_current_deals(user_id):
    try:
        # Получаем текущие скидки Steam
        steam_deals = get_steam_deals()
        if steam_deals:
            await bot.send_message(user_id, "🔥 **Текущие скидки Steam:**")
            for deal in steam_deals[:3]:  # Первые 3 скидки
                text = f"🎮 {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                await bot.send_message(user_id, text)
        
        # Получаем текущие бесплатные игры Epic
        epic_deals = get_epic_free_games()
        if epic_deals:
            await bot.send_message(user_id, "🎁 **Текущие бесплатные игры Epic:**")
            for deal in epic_deals[:3]:  # Первые 3 игры
                text = f"🎮 {deal['title']}\n🔗 {deal['url']}"
                await bot.send_message(user_id, text)
                
        if not steam_deals and not epic_deals:
            await bot.send_message(user_id, "На данный момент нет актуальных скидок.")
            
    except Exception as e:
        print(f"Error sending current deals: {e}")
        await bot.send_message(user_id, "Произошла ошибка при получении скидок.")

# Хэндлеры
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    
    await message.answer("Привет! Ты подписан на скидки Steam и бесплатные игры Epic.")
    await asyncio.sleep(1)
    await message.answer("Загружаю текущие скидки...")
    
    # Отправляем текущие скидки сразу после старта
    await send_current_deals(user_id)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 **Команды бота:**
/start - подписаться и получить текущие скидки
/help - показать это сообщение
/deals - получить текущие скидки (ручной запрос)

Бот автоматически присылает новые скидки каждые 30 минут!
    """
    await message.answer(help_text)

@dp.message(Command("deals"))
async def deals_command(message: types.Message):
    """Ручной запрос текущих скидок"""
    await message.answer("Загружаю текущие скидки...")
    await send_current_deals(message.from_user.id)

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

# Запуск бота
async def start_bot():
    print("Starting Telegram bot polling...")
    # Запускаем рассылку в фоне
    asyncio.create_task(send_deals())
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    # Запускаем и бота, и веб-сервер в одном event loop
    async def main():
        # Создаем задачу для бота
        bot_task = asyncio.create_task(start_bot())
        # Запускаем веб-сервер
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        
        # Запускаем обе задачи
        await asyncio.gather(server.serve(), bot_task)
    
    # Запускаем всё
    asyncio.run(main())