from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from session_manager import session_manager

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    session = session_manager.get(user_id)
    session.clear()

    text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men <b>_yuklaydi_bot</b> — barcha tarmoqlardan video yuklovchi universal botman! 🎬⚡️\n\n"
        "📥 <b>Qayerlardan video yuklay olaman:</b>\n"
        "• 🔴 <b>YouTube & Shorts:</b> Havola yuboring, istalgan videoni yuklab beraman.\n"
        "• 🔵 <b>Telegram:</b> Kanallardagi post havolalarini (<code>https://t.me/...</code>) yoki forward qilingan videolarni toza qilib yuklab beraman!\n"
        "• 🟣 <b>Instagram & TikTok:</b> Reels va videolarni suv belgisiz (watermark-siz) yuklab beraman.\n\n"
        "🖼 <b>Rasmlardan video yasash:</b>\n"
        "• Menga bir nechta rasm yuboring, ularni bir-biriga ulab, romantik musiqa bilan video qilib beraman!\n\n"
        "<i>Boshlash uchun video havolasini yoki rasmlaringizni yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Botdan foydalanish:</b>\n\n"
        "📥 <b>Video yuklash:</b>\n"
        "1. YouTube, Instagram, TikTok yoki Telegram kanalidagi havola (link)ni yuboring.\n"
        "2. Yoki Telegramdagi istalgan videoni botga <b>Forward (Uzatish)</b> qilib tashlang — bot uni toza holda saqlab beradi.\n\n"
        "🎬 <b>Rasmlardan video montaj:</b>\n"
        "Bir nechta rasmni bitta albom qilib tashlang, bot avtomatik video tayyorlaydi.\n\n"
        "🔄 Yangitdan boshlash: /reset"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    session_manager.get(user_id).clear()
    await message.answer("🗑 Tozalandi. Yangi havola yoki rasmlarni yuborishingiz mumkin.")
