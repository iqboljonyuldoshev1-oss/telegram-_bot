import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from session_manager import session_manager
from video_maker import render_slideshow
from keyboards import (
    get_control_keyboard,
    get_style_keyboard,
    get_aspect_keyboard,
    get_duration_keyboard,
    STYLE_NAMES,
    ASPECT_NAMES,
    DURATION_NAMES
)

router = Router()


@router.callback_query(F.data == "btn_render")
async def cb_render_video(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    session = session_manager.get(user_id)

    if len(session.photos) < 2:
        await callback.answer(
            "⚠️ Video yaratish uchun kamida 2 ta rasm yuborishingiz kerak!",
            show_alert=True
        )
        return

    await callback.answer()
    status_msg = await callback.message.answer(
        "⏳ <b>Video montaj qilinmoqda...</b>\n"
        "<i>Kadrlar birlashtirilmoqda, effektlar qo'llanmoqda va MP4 formatga o'tkazilmoqda. "
        "Biroz kuting...</i>",
        parse_mode="HTML"
    )

    output_file = str(session.user_dir / f"result_{user_id}.mp4")

    try:
        # Run CPU-intensive rendering in thread pool to prevent blocking asyncio
        await asyncio.to_thread(
            render_slideshow,
            image_paths=list(session.photos),
            output_path=output_file,
            audio_path=session.audio,
            aspect_ratio=session.aspect,
            style=session.style,
            slide_duration=session.duration,
            transition_duration=0.6,
            fps=30
        )

        caption = (
            f"🎬 <b>Sizning videongiz tayyor bo'ldi!</b>\n\n"
            f"🖼 <b>Rasmlar soni:</b> {len(session.photos)} ta\n"
            f"🎨 <b>Uslub:</b> {STYLE_NAMES.get(session.style, session.style)}\n"
            f"📐 <b>O'lcham:</b> {ASPECT_NAMES.get(session.aspect, session.aspect)}\n"
            f"⏱ <b>Kadr vaqti:</b> {session.duration}s\n"
            f"🎵 <b>Musiqa:</b> {'Bor' if session.audio else 'Yoq'}\n\n"
            f"<i>Yangi video yasash uchun shunchaki yana yangi rasmlar yuboring!</i>"
        )

        video_input = FSInputFile(output_file)
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=video_input,
            caption=caption,
            parse_mode="HTML",
            supports_streaming=True
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Videoni tayyorlashda xatolik yuz berdi:\n<code>{str(e)}</code>", parse_mode="HTML")
    finally:
        # Clean up temporary result video file
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass


@router.callback_query(F.data == "menu_style")
async def cb_menu_style(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    await callback.message.edit_text(
        "🎨 <b>Video uslubini (o'tish effektini) tanlang:</b>\n\n"
        "• <b>Kino (Ken Burns):</b> Sekin yaqinlashish va crossfade, juda chiroyli va professional ko'rinish.\n"
        "• <b>Yumshoq Crossfade:</b> Rasmlar bir-biriga muloyim erib o'tadi.\n"
        "• <b>Slayd:</b> Rasmlar yon tomonga siljib almashadi.\n"
        "• <b>Dinamik Flash:</b> Qisqa oq chaqnash bilan ritmik o'tish.",
        reply_markup=get_style_keyboard(session.style),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_style:"))
async def cb_set_style(callback: CallbackQuery):
    style_key = callback.data.split(":")[1]
    session = session_manager.get(callback.from_user.id)
    session.style = style_key
    await callback.answer("✅ Uslub o'zgartirildi!")
    await show_main_panel(callback)


@router.callback_query(F.data == "menu_aspect")
async def cb_menu_aspect(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    await callback.message.edit_text(
        "📐 <b>Video formatini (o'lchamini) tanlang:</b>\n\n"
        "• <b>📱 9:16:</b> Instagram Reels, TikTok, YouTube Shorts va Stories uchun.\n"
        "• <b>🖥 16:9:</b> Kompyuter, televizor va YouTube gorizontal videolari uchun.\n"
        "• <b>⏹ 1:1:</b> Kvadrat format (Instagram post va boshqalar).",
        reply_markup=get_aspect_keyboard(session.aspect),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_aspect:"))
async def cb_set_aspect(callback: CallbackQuery):
    aspect_key = callback.data.split(":")[1]
    session = session_manager.get(callback.from_user.id)
    session.aspect = aspect_key
    await callback.answer("✅ O'lcham o'zgartirildi!")
    await show_main_panel(callback)


@router.callback_query(F.data == "menu_duration")
async def cb_menu_duration(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    await callback.message.edit_text(
        "⏱ <b>Har bir rasm ekranda qancha vaqt turishini tanlang:</b>",
        reply_markup=get_duration_keyboard(str(session.duration)),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_duration:"))
async def cb_set_duration(callback: CallbackQuery):
    dur_str = callback.data.split(":")[1]
    session = session_manager.get(callback.from_user.id)
    session.duration = float(dur_str)
    await callback.answer("✅ Vaqt o'zgartirildi!")
    await show_main_panel(callback)


@router.callback_query(F.data == "menu_audio_info")
async def cb_audio_info(callback: CallbackQuery):
    await callback.answer(
        "🎵 Videoga musiqa qo'shish uchun shunchaki botga istalgan MP3 musiqa yoki ovozli xabar (voice) yuboring!",
        show_alert=True
    )


@router.callback_query(F.data == "menu_back")
async def cb_menu_back(callback: CallbackQuery):
    await show_main_panel(callback)
    await callback.answer()


@router.callback_query(F.data == "btn_clear")
async def cb_clear(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    session.clear()
    await callback.answer("🗑 Tozalandi!", show_alert=True)
    await callback.message.edit_text(
        "🗑 Barcha rasmlar va musiqa tozalandi.\n\n"
        "Yangi video yaratish uchun menga yangi rasmlar yuboring!"
    )


async def show_main_panel(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
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
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

