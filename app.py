import logging
from fastapi import FastAPI, Request
from aiogram import Bot
from aiogram.types import Update

from config import load_config
import db
from bot import build_dispatcher

logging.basicConfig(level=logging.INFO)

cfg = load_config()
bot = Bot(token=cfg.bot_token)
dp = build_dispatcher(cfg)
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    db.init_db()
    db.seed_demo_products()
    # Telegram будет слать апдейты на этот URL (webhook) :contentReference[oaicite:1]{index=1}
    await bot.set_webhook(cfg.webhook_url)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook(drop_pending_updates=True)

@app.post(cfg.webhook_path)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
