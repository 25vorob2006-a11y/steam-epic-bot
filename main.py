import asyncio
import os
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN, CHECK_INTERVAL_STEAM, CHECK_INTERVAL_EPIC
from steam_parser import get_steam_deals
from epic_parser import get_epic_free_games
from database import add_user, get_users, save_deal, is_new_deal

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ... (весь ваш код с клавиатурами и хэндлерами остается без изменений) ...

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

# Вебхук роуты
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"https://your-app.onrender.com/webhook")
    asyncio.create_task(send_deals())

@app.post("/webhook")
async def webhook(request: dict):
    """Эндпоинт для вебхуков от Telegram"""
    telegram_update = types.Update(**request)
    await dp.feed_webhook_update(bot, telegram_update)

@app.get("/")
def root():
    return {"status": "Bot is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Для вебхуков используем uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)