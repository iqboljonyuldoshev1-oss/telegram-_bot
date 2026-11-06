import os
from aiogram import Router, F, Bot
from aiogram.types import Message
from session_manager import session_manager
from keyboards import get_control_keyboard

router = Router()


async def send_or_update_control_panel(bot: Bot, chat_id: int, user_id: int):
    session = session_manager.get(user_id)
    photo_count = len(session.photos)
    has_audio = session.audio is not None

    audio_text = "✅ Musiqa biriktirilgan" if has_audio else "❌ Musiqa yo'q (ixtiyoriy: MP3 yuborishingiz mumkin)"
    text = (
        f"📸 <b>Yuklangan rasmlar:</b> {photo_count} ta\n"
        f"🎵 <b>Audio:</b> {audio_text}\n\n"
        f"⚙️ <i>Pastdagi tugmalar orqali videoning ko'rinishini va parametrlarini sozlashingiz mumkin. "
        f"Tayyor bo'lgach, «🎬 Videoni yaratish» tugmasini bosing!</i>"
    )
    keyboard = get_control_keyboard(
        style=session.style,
        aspect=session.aspect,
        duration=str(session.duration),
        photo_count=photo_count,
        has_audio=has_audio
    )

    # Try updating existing control message or send a new one
    if session.control_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=session.control_msg_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    session.control_msg_id = msg.message_id


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    # Get highest resolution photo
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)

    file_idx = len(session.photos) + 1
    dest_path = session.user_dir / f"photo_{file_idx}.jpg"

    await bot.download_file(file_info.file_path, destination=dest_path)
    session.add_photo(str(dest_path))

    await send_or_update_control_panel(bot, message.chat.id, user_id)


@router.message(F.audio | F.voice)
async def handle_audio(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    audio_obj = message.audio or message.voice
    file_info = await bot.get_file(audio_obj.file_id)

    ext = ".mp3" if message.audio else ".ogg"
    dest_path = session.user_dir / f"audio_{user_id}{ext}"

    await bot.download_file(file_info.file_path, destination=dest_path)
    session.set_audio(str(dest_path))

    await message.reply("🎵 Musiqa qabul qilindi! U videoga fon sifatida qo'shiladi.")
    await send_or_update_control_panel(bot, message.chat.id, user_id)


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    mime = message.document.mime_type or ""
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    if mime.startswith("image/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "img.jpg")[1] or ".jpg"
        file_idx = len(session.photos) + 1
        dest_path = session.user_dir / f"photo_{file_idx}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.add_photo(str(dest_path))
        await send_or_update_control_panel(bot, message.chat.id, user_id)

    elif mime.startswith("audio/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "audio.mp3")[1] or ".mp3"
        dest_path = session.user_dir / f"audio_{user_id}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.set_audio(str(dest_path))
        await message.reply("🎵 Audio fayl qabul qilindi!")
        await send_or_update_control_panel(bot, message.chat.id, user_id)

