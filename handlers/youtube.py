import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from youtube_downloader import is_downloadable_url, extract_url, download_video_link
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


@router.message(F.text.func(lambda text: is_downloadable_url(text)))
async def handle_media_link(message: Message, bot: Bot):
    url = extract_url(message.text)
    if not url:
        return

    user_id = message.from_user.id
    session = session_manager.get(user_id)

    status_msg = await message.reply(
        "⏳ <b>Video yuklab olinmoqda (100 MB gacha ruxsat)...</b>\n"
        "<i>Biroz kuting, hozir video sizga yuboriladi...</i>",
        parse_mode="HTML"
    )

    try:
        data = await asyncio.to_thread(
            download_video_link,
            url=url,
            download_dir=str(session.user_dir)
        )

        file_path = data["file_path"]
        title = data.get("title", "Video")
        channel = data.get("channel", "Yuklandi")
        duration_str = format_duration(data.get("duration", 0))
        orig_mb = data.get("orig_size_mb", 0)

        size_note = f"📦 <b>Hajmi:</b> {orig_mb} MB\n" if orig_mb else ""

        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"⏱ <b>Davomiyligi:</b> {duration_str}\n"
            f"👤 <b>Kanal/Manba:</b> {channel}\n"
            f"{size_note}\n"
            f"📥 <i><b>_yuklaydi_bot</b> orqali yuklab olindi.</i>"
        )

        video_input = FSInputFile(file_path)
        await message.reply_video(
            video=video_input,
            caption=caption,
            parse_mode="HTML",
            supports_streaming=True
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        error_msg = str(e)
        if "100" in error_msg.lower() or "max_filesize" in error_msg.lower() or "katta" in error_msg.lower():
            await status_msg.edit_text(
                "❌ <b>Kechirasiz, video hajmi 100 MB dan ham katta!</b>\n"
                "Iltimos, hajmi 100 MB gacha bo'lgan videolarni yuboring.",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Videoni yuklab bo'lmadi!</b>\n"
                f"Havola to'g'riligini yoki video yopiq (private) emasligini tekshiring.\n\n"
                f"<i>Sabab: {error_msg[:120]}</i>",
                parse_mode="HTML"
            )
    finally:
        if 'data' in locals() and os.path.exists(data.get("file_path", "")):
            try:
                os.remove(data["file_path"])
            except Exception:
                pass
