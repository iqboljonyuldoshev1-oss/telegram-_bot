import os
from aiogram import Router, F, Bot
from aiogram.types import Message
from session_manager import session_manager, ROMANTIC_TRACKS
from keyboards import get_control_keyboard

router = Router()


async def send_or_update_control_panel(bot: Bot, chat_id: int, user_id: int):
    session = session_manager.get(user_id)
    photo_cnt = session.photo_count
    video_cnt = session.video_count
    total_cnt = session.total_count

    if session.music_choice == "custom":
        music_name = "🎧 Shaxsiy musiqa"
    else:
        music_name = ROMANTIC_TRACKS.get(session.music_choice, "🌹 Mayin Pianino")

    text = (
        f"🎬 <b>Yuklangan medialar:</b>\n"
        f"• 📸 Rasmlar: {photo_cnt} ta\n"
        f"• 🎥 Videolar: {video_cnt} ta\n"
        f"• 🎵 Musiqa: <b>{music_name}</b>\n\n"
        f"<i>Yana rasm yoki video yuborishingiz mumkin. "
        f"Pastdagi tugmalar orqali romantik musiqa, uslub va o'lchamni tanlang, "
        f"so'ng «🎬 Videoni yaratish» tugmasini bosing!</i>"
    )

    keyboard = get_control_keyboard(
        style=session.style,
        aspect=session.aspect,
        duration=str(session.duration),
        total_count=total_cnt,
        music_choice=session.music_choice,
        has_custom_audio=(session.custom_audio is not None)
    )

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

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)

    file_idx = session.total_count + 1
    dest_path = session.user_dir / f"photo_{file_idx}.jpg"

    await bot.download_file(file_info.file_path, destination=dest_path)
    session.add_media("photo", str(dest_path))

    await send_or_update_control_panel(bot, message.chat.id, user_id)


@router.message(F.video)
async def handle_video(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    file_info = await bot.get_file(message.video.file_id)
    file_idx = session.total_count + 1
    dest_path = session.user_dir / f"video_{file_idx}.mp4"

    await bot.download_file(file_info.file_path, destination=dest_path)
    session.add_media("video", str(dest_path))

    await send_or_update_control_panel(bot, message.chat.id, user_id)


@router.message(F.audio | F.voice)
async def handle_audio(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    audio_obj = message.audio or message.voice
    file_info = await bot.get_file(audio_obj.file_id)

    ext = ".mp3" if message.audio else ".ogg"
    dest_path = session.user_dir / f"custom_audio_{user_id}{ext}"

    await bot.download_file(file_info.file_path, destination=dest_path)
    session.set_custom_audio(str(dest_path))

    await message.reply("🎵 Shaxsiy musiqangiz qabul qilindi va videoga ulandi!")
    await send_or_update_control_panel(bot, message.chat.id, user_id)


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    mime = message.document.mime_type or ""
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    if mime.startswith("image/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "img.jpg")[1] or ".jpg"
        file_idx = session.total_count + 1
        dest_path = session.user_dir / f"photo_{file_idx}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.add_media("photo", str(dest_path))
        await send_or_update_control_panel(bot, message.chat.id, user_id)

    elif mime.startswith("video/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "vid.mp4")[1] or ".mp4"
        file_idx = session.total_count + 1
        dest_path = session.user_dir / f"video_{file_idx}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.add_media("video", str(dest_path))
        await send_or_update_control_panel(bot, message.chat.id, user_id)

    elif mime.startswith("audio/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "audio.mp3")[1] or ".mp3"
        dest_path = session.user_dir / f"custom_audio_{user_id}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.set_custom_audio(str(dest_path))
        await message.reply("🎵 Shaxsiy audio qabul qilindi!")
        await send_or_update_control_panel(bot, message.chat.id, user_id)
