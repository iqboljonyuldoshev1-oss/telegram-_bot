import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from youtube_downloader import is_youtube_url, extract_youtube_url, download_youtube_video
from session_manager import session_manager

router = Router()

def format_duration(seconds: int) -> str:
    if not seconds:
        return "Noma'lum"
    mins = seconds // 60
    secs = seconds % 60
    if mins >= 60:
        hours = mins // 60
        mins = mins % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


@router.message(F.text.func(lambda text: is_youtube_url(text)))
async def handle_youtube_link(message: Message, bot: Bot):
    url = extract_youtube_url(message.text)
    if not url:
        return

    user_id = message.from_user.id
    session = session_manager.get(user_id)

    status_msg = await message.reply(
        "⏳ <b>YouTube videosi yuklab olinmoqda...</b>\n"
        "<i>Biroz kuting (huddi @yuklaydi_bot kabi tezkor yuklanadi)...</i>",
        parse_mode="HTML"
    )

    try:
        data = await asyncio.to_thread(
            download_youtube_video,
            url=url,
            download_dir=str(session.user_dir)
        )

        file_path = data["file_path"]
        title = data.get("title", "YouTube Video")
        channel = data.get("channel", "YouTube")
        duration_str = format_duration(data.get("duration", 0))

        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"⏱ <b>Davomiyligi:</b> {duration_str}\n"
            f"👤 <b>Kanal:</b> {channel}\n\n"
            f"📥 <i><b>_yuklaydi_bot</b> orqali yuklab olindi.</i>"
        )

        video_input = FSInputFile(file_path)
        await message.reply_video(
            video=video_input,
            caption=caption,
            parse_mode="HTML",
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        error_msg = str(e)
        if "max_filesize" in error_msg.lower() or "file is too large" in error_msg.lower():
            await status_msg.edit_text(
                "❌ <b>Kechirasiz, video hajmi juda katta!</b>\n"
                "Telegram botlari orqali maksimal 50 MB gacha bo'lgan videolarni yuklash mumkin.",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Videoni yuklab bo'lmadi!</b>\n"
                f"Havola to'g'riligini yoki video yopiq (private) emasligini tekshiring.\n"
                f"<code>Xatolik: {error_msg[:150]}</code>",
                parse_mode="HTML"
            )
    finally:
        # Clean up downloaded file
        if 'data' in locals() and os.path.exists(data.get("file_path", "")):
            try:
                os.remove(data["file_path"])
            except Exception:
                pass

