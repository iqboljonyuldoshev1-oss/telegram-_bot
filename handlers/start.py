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
        "Men sizning rasmlaringiz va videolaringizdan <b>chiroyli romantik videolar</b> yaratib beruvchi botman! 🎬✨\n\n"
        "💖 <b>Asosiy yangi imkoniyatlar:</b>\n"
        "🌹 <b>Romantik musiqalar:</b> Bot ichida maxsus mayin pianino, sokin romantika va akustik sevgi kuylari tayyor turibdi (yoki o'zingiz ham musiqa yuborishingiz mumkin)!\n"
        "🎥 <b>Videolarni qabul qilish:</b> Endi nafaqat rasmlar, balki qisqa videolarni ham yuborishingiz mumkin! Bot ularni bir-biriga chiroyli ulab beradi.\n"
        "🚫 <b>Sun'iy intellekt buzilishlarisiz:</b> Rasmlar va videolaringiz asl tiniqligi saqlanadi.\n"
        "📱 <b>Reels/TikTok (9:16) va boshqa formatlar.</b>\n\n"
        "🚀 <b>Boshlash uchun:</b> Menga xohlagan rasmlaringiz yoki videolaringizni yuboring!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Botdan foydalanish yo'riqnomasi:</b>\n\n"
        "1️⃣ Menga o'zingiz xohlagan <b>rasmlar yoki videolarni</b> yuboring (kamida 1-2 ta).\n"
        "2️⃣ <b>«🎵 Musiqa»</b> tugmasi orqali romantik kuylardan birini tanlang (yoki o'zingiz MP3 yuboring).\n"
        "3️⃣ Video uslubi va formatini (9:16, 16:9, 1:1) tanlang.\n"
        "4️⃣ <b>«🎬 Videoni yaratish»</b> tugmasini bosing va tayyor rolikni qabul qiling!\n\n"
        "🔄 Yangitdan boshlash uchun: /reset"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    session_manager.get(user_id).clear()
    await message.answer("🗑 Barcha yuklangan fayllar va sozlamalar tozalandi. Yangi rasm yoki videolarni yuborishingiz mumkin.")
