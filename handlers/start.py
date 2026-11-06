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
        "Men sizning rasmlaringizdan <b>yuqori sifatli professional video</b> tayyorlab beruvchi botman! 🎬\n\n"
        "✨ <b>Asosiy imkoniyatlar:</b>\n"
        "🚫 <b>Sun'iy intellekt buzilishlarisiz:</b> Rasmlaringiz asl tiniqligi saqlanadi, yuzlar buzilmaydi va g'alati narsalar qo'shilmaydi.\n"
        "🎥 <b>Professional effektlar:</b> Kino uslubidagi sekin yaqinlashish (Ken Burns), yumshoq crossfade, dinamik slaydlar.\n"
        "📱 <b>Barcha formatlar:</b> Reels/TikTok (9:16), YouTube (16:9) va Kvadrat (1:1).\n"
        "🎵 <b>Musiqa:</b> Sevimli qo'shig'ingizni audio qilib yuboring, videoga avtomatik ulab beriladi!\n\n"
        "🚀 <b>Boshlash uchun:</b> Menga 2 yoki undan ko'p rasm yuboring (bittalab yoki albom qilib)!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Botdan foydalanish yo'riqnomasi:</b>\n\n"
        "1️⃣ Menga o'zingiz xohlagan rasmlarni yuboring (kamida 2 ta).\n"
        "2️⃣ (Ixtiyoriy) Agar musiqa qo'shmoqchi bo'lsangiz, MP3 musiqa yoki ovozli xabar yuboring.\n"
        "3️⃣ Rasmlar ostidagi tugmalar orqali video uslubini (Kino, Yumshoq, Slayd), formatini (9:16, 16:9, 1:1) va tezligini tanlang.\n"
        "4️⃣ <b>«🎬 Videoni yaratish»</b> tugmasini bosing va bir necha soniyada tayyor videoni qabul qiling!\n\n"
        "🔄 Yangitdan boshlash uchun: /reset"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    session_manager.get(user_id).clear()
    await message.answer("🗑 Barcha yuklangan rasmlar va sozlamalar tozalandi. Yangi rasmlarni yuborishingiz mumkin.")

