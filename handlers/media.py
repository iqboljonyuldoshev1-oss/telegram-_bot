import os
import uuid
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message
from session_manager import session_manager, ROMANTIC_TRACKS
from keyboards import get_control_keyboard
from handlers.video import do_render_and_send

router = Router()


async def on_media_batch_finished(user_id: int, chat_id: int, bot: Bot):
    """
    Called after debounce delay (2.0s) when user finishes sending an album or multiple photos.
    Automatically connects all photos together into a video!
    """
    await asyncio.sleep(2.0)
    session = session_manager.get(user_id)

    # If user sent 2 or more photos/videos: automatically prepare the video!
    if session.total_count >= 2:
        await do_render_and_send(user_id, chat_id, bot)
    elif session.total_count == 1:
        text = (
            f"📸 <b>1 ta rasm qabul qilindi.</b>\n\n"
            f"<i>Videolar tayyorlanishi uchun menga yana bir nechta rasm yuboring! "
            f"Barcha yuborgan rasmlaringiz bir-biriga ulanib, chiroyli video qilib beriladi.</i>"
        )
        keyboard = get_control_keyboard(
            style=session.style,
            aspect=session.aspect,
            duration=str(session.duration),
            total_count=session.total_count,
            music_choice=session.music_choice,
            has_custom_audio=(session.custom_audio is not None)
        )
        msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        session.control_msg_id = msg.message_id


def schedule_debounce(user_id: int, chat_id: int, bot: Bot):
    session = session_manager.get(user_id)
    if session.debounce_task and not session.debounce_task.done():
        session.debounce_task.cancel()
    session.debounce_task = asyncio.create_task(on_media_batch_finished(user_id, chat_id, bot))


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    # Unique filename avoids concurrent download conflicts in albums
    unique_id = uuid.uuid4().hex[:10]
    dest_path = session.user_dir / f"photo_{unique_id}.jpg"

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    await bot.download_file(file_info.file_path, destination=dest_path)

    session.add_media("photo", str(dest_path))
    schedule_debounce(user_id, message.chat.id, bot)


@router.message(F.video)
async def handle_video(message: Message, bot: Bot):
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    unique_id = uuid.uuid4().hex[:10]
    dest_path = session.user_dir / f"video_{unique_id}.mp4"

    file_info = await bot.get_file(message.video.file_id)
    await bot.download_file(file_info.file_path, destination=dest_path)

    session.add_media("video", str(dest_path))
    schedule_debounce(user_id, message.chat.id, bot)


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

    await message.reply("🎵 Shaxsiy musiqangiz qabul qilindi! Keyingi videolarga ushbu musiqa qo'shiladi.")


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    mime = message.document.mime_type or ""
    user_id = message.from_user.id
    session = session_manager.get(user_id)

    if mime.startswith("image/"):
        unique_id = uuid.uuid4().hex[:10]
        ext = os.path.splitext(message.document.file_name or "img.jpg")[1] or ".jpg"
        dest_path = session.user_dir / f"photo_{unique_id}{ext}"

        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination=dest_path)

        session.add_media("photo", str(dest_path))
        schedule_debounce(user_id, message.chat.id, bot)

    elif mime.startswith("video/"):
        unique_id = uuid.uuid4().hex[:10]
        ext = os.path.splitext(message.document.file_name or "vid.mp4")[1] or ".mp4"
        dest_path = session.user_dir / f"video_{unique_id}{ext}"

        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination=dest_path)

        session.add_media("video", str(dest_path))
        schedule_debounce(user_id, message.chat.id, bot)

    elif mime.startswith("audio/"):
        file_info = await bot.get_file(message.document.file_id)
        ext = os.path.splitext(message.document.file_name or "audio.mp3")[1] or ".mp3"
        dest_path = session.user_dir / f"custom_audio_{user_id}{ext}"

        await bot.download_file(file_info.file_path, destination=dest_path)
        session.set_custom_audio(str(dest_path))
        await message.reply("🎵 Shaxsiy audio qabul qilindi!")
