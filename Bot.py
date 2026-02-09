import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))  # -1001234567890

bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

user_captchas: Dict[int, Dict] = {}  # Простое хранение

@router.message(CommandStart())
async def start_captcha(message: Message):
    a, b = random.randint(1, 20), random.randint(1, 20)
    answer = a + b
    task = f"✅ Решите капчу для ссылки в группу: {a} + {b} = ?"
    
    user_captchas[message.from_user.id] = {"answer": answer, "time": datetime.now()}
    await message.answer(task)
    logger.info(f"Капча для {message.from_user.id}: {answer}")

@router.message(F.text)
async def check_captcha(message: Message):
    user_id = message.from_user.id
    if user_id not in user_captchas:
        return await message.answer("❌ Сначала /start!")
    
    captcha = user_captchas[user_id]
    if (datetime.now() - captcha["time"]).seconds > 300:  # 5 мин таймаут
        del user_captchas[user_id]
        return await message.answer("⏰ Время вышло. /start заново.")
    
    if message.text.strip().isdigit() and int(message.text) == captcha["answer"]:
        try:
            expire_date = int((datetime.now() + timedelta(minutes=5)).timestamp())
            link_data = await bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name=f"captcha_{user_id}",
                expire_date=expire_date,
                member_limit=1
            )
            await message.answer(f"🎉 Капча пройдена!\n🔗 {link_data.invite_link}\n(5 мин, 1 чел.)")
            logger.info(f"Ссылка выдана {user_id}")
        except Exception as e:
            await message.answer("❌ Ошибка создания ссылки. Админ проверит.")
            logger.error(f"Ошибка: {e}")
        finally:
            del user_captchas[user_id]
    else:
        await message.answer("❌ Неверно! Попробуйте ещё раз.")

async def main():
    if not TOKEN or GROUP_ID == 0:
        logger.error("Установите TOKEN и GROUP_ID в .env")
        return
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
