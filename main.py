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

# Хэндлеры
@dp.message(Command("start"))
async def start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer("Привет! Ты подписан на скидки Steam и бесплатные игры Epic.")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("/start - подписаться\n/help - помощь")

# Функция для рассылки
async def send_deals():
    while True:
        try:
            users = get_users()
            
            # Steam
            steam_deals = get_steam_deals()
            for deal in steam_deals:
                if is_new_deal("steam_" + deal["id"]):
                    for user in users:
                        text = f"🔥 Steam Deal: {deal['title']}\n💰 {deal['original_price']} → {deal['final_price']} ({deal['discount']}%)\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("steam_" + deal["id"])
            
            # Epic
            epic_deals = get_epic_free_games()
            for deal in epic_deals:
                if is_new_deal("epic_" + deal["id"]):
                    for user in users:
                        text = f"🎁 Free Epic Game: {deal['title']}\n🔗 {deal['url']}"
                        await bot.send_message(user, text)
                    save_deal("epic_" + deal["id"])
            
            await asyncio.sleep(min(CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC))
        except Exception as e:
            print(f"Error in send_deals: {e}")
            await asyncio.sleep(60)

# FastAPI роуты
@app.get("/")
def root():
    return {"status": "Bot is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Запуск бота без многопоточности
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