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

# FastAPI для Render
app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

async def main():
    asyncio.create_task(send_deals())
    await dp.start_polling(bot)

if __name__ == "__main__":
    # запускаем веб-сервер и Telegram-бота параллельно
    port = int(os.environ.get("PORT", 8000))
    asyncio.run(asyncio.gather(
        main(),
        uvicorn.run(app, host="0.0.0.0", port=port)
    ))
