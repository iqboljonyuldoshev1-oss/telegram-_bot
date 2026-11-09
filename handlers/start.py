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
        "Men <b>_yuklaydi_bot</b> — YouTube videolarini yuklovchi va rasmlardan video yaratuvchi botman! 🎬⚡️\n\n"
        "🚀 <b>Asosiy imkoniyatlar:</b>\n\n"
        "1️⃣ <b>YouTube dan video yuklash:</b>\n"
        "• Menga istalgan <b>YouTube</b> yoki <b>Shorts</b> havolasini yuboring.\n"
        "• Bot videoni eng yuqori sifatda bir necha soniyada sizga tashlab beradi!\n\n"
        "2️⃣ <b>Rasmlardan video tayyorlash:</b>\n"
        "• Menga bir nechta rasm yuboring (albom qilib).\n"
        "• Barcha rasmlaringiz bir-biriga ulanib, romantik musiqa bilan chiroyli video montaj qilinadi!\n\n"
        "<i>Boshlash uchun YouTube havolasini yoki rasmlaringizni yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Botdan foydalanish:</b>\n\n"
        "📥 <b>YouTube yuklash:</b>\n"
        "Istalgan YouTube videosining havolasini (masalan: <code>https://youtu.be/...</code> yoki Shorts) yuboring. Bot uni yuklab beradi.\n\n"
        "🎬 <b>Video yasash:</b>\n"
        "2 yoki undan ortiq rasmlarni tanlab bitta albom qilib tashlang. Bot ularni avtomatik ulab beradi.\n\n"
        "🔄 Yangitdan boshlash: /reset"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    session_manager.get(user_id).clear()
    await message.answer("🗑 Barcha yuklangan fayllar tozalandi. Yangi havola yoki rasmlarni yuborishingiz mumkin.")
