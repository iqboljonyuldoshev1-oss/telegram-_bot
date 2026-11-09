import os
import re
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from youtube_downloader import is_downloadable_url, extract_url, download_video_link
from session_manager import session_manager

logger = logging.getLogger(__name__)
router = Router()

TELEGRAM_LINK_PATTERN = re.compile(r'https?://t\.me/([a-zA-Z0-9_]+)/(\d+)', re.IGNORECASE)

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


# 1. Handle Telegram post links (e.g. https://t.me/channel_name/123)
@router.message(F.text.func(lambda text: bool(TELEGRAM_LINK_PATTERN.search(text or ""))))
async def handle_telegram_link(message: Message, bot: Bot):
    match = TELEGRAM_LINK_PATTERN.search(message.text)
    if not match:
        return

    channel_username = match.group(1)
    post_id = int(match.group(2))

    status_msg = await message.reply(
        "⏳ <b>Telegram videosi ochilmoqda...</b>\n<i>Iltimos, kuting...</i>",
        parse_mode="HTML"
    )

    try:
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=f"@{channel_username}",
            message_id=post_id,
            caption="📥 <i><b>_yuklaydi_bot</b> orqali yuklab olindi.</i>",
            parse_mode="HTML"
        )
        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Telegram link error: {e}")
        error_text = str(e).lower()
        if "chat not found" in error_text or "message not found" in error_text:
            await status_msg.edit_text(
                "❌ <b>Xabar topilmadi!</b>\n"
                "Kanal ochiq (public) ekanligini yoki xabar o'chirilmaganini tekshiring.\n"
                "<i>Yoki videoni to'g'ridan-to'g'ri ushbu botga 'Forward' (Uzatish) qilib yuboring!</i>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Telegram videosini ochib bo'lmadi:</b>\n<code>{str(e)[:150]}</code>\n\n"
                f"<i>Maslahat: Videoni to'g'ridan-to'g'ri botga forward qilib yuboring!</i>",
                parse_mode="HTML"
            )


# 2. Handle forwarded video / video note from other channels or chats
@router.message(F.forward_origin & (F.video | F.video_note | F.document))
async def handle_forwarded_media(message: Message, bot: Bot):
    status_msg = await message.reply("⏳ <b>Telegram media toza holda saqlanmoqda...</b>", parse_mode="HTML")
    try:
        if message.video:
            await message.reply_video(
                video=message.video.file_id,
                caption="📥 <i><b>_yuklaydi_bot</b> orqali toza holda saqlandi.</i>",
                parse_mode="HTML",
                supports_streaming=True
            )
        elif message.video_note:
            await message.reply_video_note(
                video_note=message.video_note.file_id
            )
        elif message.document:
            await message.reply_document(
                document=message.document.file_id,
                caption="📥 <i><b>_yuklaydi_bot</b> orqali saqlandi.</i>",
                parse_mode="HTML"
            )
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Forwarded media error: {e}")
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)[:150]}")


# 3. Handle YouTube, Instagram, TikTok and other web video links
@router.message(F.text.func(lambda text: is_downloadable_url(text)))
async def handle_media_link(message: Message, bot: Bot):
    url = extract_url(message.text)
    if not url:
        return

    user_id = message.from_user.id
    session = session_manager.get(user_id)

    status_msg = await message.reply(
        "⏳ <b>Video yuklab olinmoqda...</b>\n"
        "<i>Biroz kuting, video tayyorlanmoqda...</i>",
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

        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"⏱ <b>Davomiyligi:</b> {duration_str}\n"
            f"👤 <b>Kanal/Manba:</b> {channel}\n\n"
            f"📥 <i><b>_yuklaydi_bot</b> orqali yuklab olindi.</i>"
        )

        video_input = FSInputFile(file_path)
        try:
            # First try send as playable video
            await message.reply_video(
                video=video_input,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True
            )
        except Exception as vid_err:
            logger.warning(f"send_video failed, falling back to send_document: {vid_err}")
            # Fallback to send as document
            await message.reply_document(
                document=video_input,
                caption=caption,
                parse_mode="HTML"
            )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Download video error: {e}", exc_info=True)
        error_msg = str(e)
        await status_msg.edit_text(
            f"❌ <b>Videoni yuklab bo'lmadi!</b>\n\n"
            f"<i>Xatolik: {error_msg[:150]}</i>",
            parse_mode="HTML"
        )
    finally:
        if 'data' in locals() and os.path.exists(data.get("file_path", "")):
            try:
                os.remove(data["file_path"])
            except Exception:
                pass
