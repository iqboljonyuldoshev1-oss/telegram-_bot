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
        "Men bir nechta rasmlar va videolarni <b>bir-biriga ulab, ajoyib video</b> tayyorlab beruvchi botman! 🎬✨\n\n"
        "🌟 <b>Qanday ishlaydi:</b>\n"
        "1️⃣ Menga <b>bir nechta rasm</b> (yoki video) yuboring (masalan: 3 ta, 5 ta, 10 ta albom qilib).\n"
        "2️⃣ Bot barcha yuborilgan rasmlarni qabul qilib, ularni bir-biriga ulaydi va foniga yoqimli romantik musiqa qo'shib video qilib beradi!\n"
        "3️⃣ Tayyor videoni qabul qilasiz va xohlasangiz uslubini, musiqasini yoki o'lchamini bitta tugma bilan o'zgartirishingiz mumkin.\n\n"
        "🚀 <b>Boshlash uchun:</b> Menga hoziroq bir nechta rasm yuboring!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Qo'llanma:</b>\n\n"
        "• <b>Bir nechta rasm yuborish:</b> Galereyangizdan bir nechta (kamida 2 ta) rasmni tanlab, bitta albom qilib botga yuboring.\n"
        "• Bot barcha rasmlarni avtomatik bir-biriga ulab videoni tayyorlaydi.\n"
        "• Agar xohlasangiz, o'zingiz yoqtirgan MP3 musiqani ham yuborishingiz mumkin.\n\n"
        "🔄 Yangitdan boshlash uchun: /reset"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    session_manager.get(user_id).clear()
    await message.answer("🗑 Barcha yuklangan fayllar tozalandi. Yangi rasmlarni yuborishingiz mumkin.")
