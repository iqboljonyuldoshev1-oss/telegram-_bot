import os
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from session_manager import session_manager, ROMANTIC_TRACKS
from video_maker import render_slideshow
from keyboards import (
    get_control_keyboard,
    get_music_keyboard,
    get_style_keyboard,
    get_aspect_keyboard,
    get_duration_keyboard,
    STYLE_NAMES,
    ASPECT_NAMES
)

router = Router()


async def do_render_and_send(user_id: int, chat_id: int, bot: Bot) -> bool:
    """Core function to render all collected photos and videos into one seamless video"""
    session = session_manager.get(user_id)

    if session.total_count < 2:
        return False

    if session.is_rendering:
        return False

    session.is_rendering = True

    status_msg = await bot.send_message(
        chat_id=chat_id,
        text=(
            f"⏳ <b>{session.total_count} ta rasm/media qabul qilindi!</b>\n"
            f"<i>Ular bir-biriga ulanmoqda, romantik musiqa va o'tish effektlari bilan "
            f"yuqori sifatli video tayyorlanmoqda. Biroz kuting...</i>"
        ),
        parse_mode="HTML"
    )

    output_file = str(session.user_dir / f"result_{user_id}.mp4")

    # Adaptive duration for large albums
    item_count = session.total_count
    slide_dur = session.duration
    if item_count >= 10:
        slide_dur = min(session.duration, 2.0)
    elif item_count >= 5:
        slide_dur = min(session.duration, 2.5)

    try:
        # Run rendering in thread pool to prevent blocking asyncio
        await asyncio.to_thread(
            render_slideshow,
            media_items=list(session.media_items),
            output_path=output_file,
            audio_path=session.effective_audio_path,
            aspect_ratio=session.aspect,
            style=session.style,
            slide_duration=slide_dur,
            transition_duration=0.6,
            fps=30
        )

        music_name = "🎧 Shaxsiy musiqa" if session.music_choice == "custom" else ROMANTIC_TRACKS.get(session.music_choice, "🌹 Mayin Pianino")

        caption = (
            f"🎬 <b>{session.total_count} ta rasmingiz bir-biriga ulanib, video tayyor bo'ldi! ✨</b>\n\n"
            f"📸 <b>Rasmlar:</b> {session.photo_count} ta\n"
            f"🎥 <b>Videolar:</b> {session.video_count} ta\n"
            f"🎵 <b>Musiqa:</b> {music_name}\n"
            f"🎨 <b>Uslub:</b> {STYLE_NAMES.get(session.style, session.style)}\n"
            f"📐 <b>O'lcham:</b> {ASPECT_NAMES.get(session.aspect, session.aspect)}\n\n"
            f"✨ <i><b>_yuklaydi_bot</b> orqali tayyorlandi.</i>"
        )

        keyboard = get_control_keyboard(
            style=session.style,
            aspect=session.aspect,
            duration=str(session.duration),
            total_count=session.total_count,
            music_choice=session.music_choice,
            has_custom_audio=(session.custom_audio is not None)
        )

        video_input = FSInputFile(output_file)
        await bot.send_video(
            chat_id=chat_id,
            video=video_input,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML",
            supports_streaming=True
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
        return True

    except Exception as e:
        await status_msg.edit_text(f"❌ Videoni tayyorlashda xatolik yuz berdi:\n<code>{str(e)}</code>", parse_mode="HTML")
        return False
    finally:
        session.is_rendering = False
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass


@router.callback_query(F.data == "btn_render")
async def cb_render_video(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    session = session_manager.get(user_id)

    if session.total_count < 2:
        await callback.answer(
            "⚠️ Video yaratish uchun kamida 2 ta rasm yoki video kerak!",
            show_alert=True
        )
        return

    await callback.answer()
    await do_render_and_send(user_id, callback.message.chat.id, bot)


@router.callback_query(F.data == "menu_music")
async def cb_menu_music(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    await callback.message.edit_text(
        "🎵 <b>Videoga romantik fon musiqasini tanlang:</b>\n\n"
        "• <b>🌹 Mayin Pianino:</b> Hissiyotli va mayin pianino ohangi.\n"
        "• <b>💕 Akustik Sevgi:</b> Chiroyli va romantik gitara ohangi.\n"
        "• <b>✨ Sokin Romance:</b> Sehrli va sokin kechki romantika.\n"
        "• <b>🎧 Shaxsiy:</b> O'zingiz yoqtirgan MP3 yoki ovoz yuborishingiz mumkin.",
        reply_markup=get_music_keyboard(session.music_choice, session.custom_audio is not None),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_music:"))
async def cb_set_music(callback: CallbackQuery):
    choice = callback.data.split(":")[1]
    session = session_manager.get(callback.from_user.id)
    session.music_choice = choice
    await callback.answer("✅ Musiqa tanlandi!")
    await show_main_panel(callback)


@router.callback_query(F.data == "menu_style")
async def cb_menu_style(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    await callback.message.edit_text(
        "🎨 <b>Video uslubini (o'tish effektini) tanlang:</b>\n\n"
        "• <b>Kino (Ken Burns):</b> Sekin yaqinlashish va crossfade, romantik va professional ko'rinish.\n"
        "• <b>Yumshoq Crossfade:</b> Rasmlar va videolar bir-biriga muloyim erib o'tadi.\n"
        "• <b>Slayd:</b> Yon tomonga silliq siljish.\n"
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
        "⏱ <b>Har bir rasm/video parchasi ekranda qancha vaqt turishini tanlang:</b>",
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
        "🗑 Barcha yuklangan rasmlar tozalandi.\n\n"
        "Yangi video yaratish uchun bir nechta rasm yuboring!"
    )


async def show_main_panel(callback: CallbackQuery):
    session = session_manager.get(callback.from_user.id)
    music_name = "🎧 Shaxsiy musiqa" if session.music_choice == "custom" else ROMANTIC_TRACKS.get(session.music_choice, "🌹 Mayin Pianino")

    text = (
        f"🎬 <b>Yuklangan medialar:</b>\n"
        f"• 📸 Rasmlar: {session.photo_count} ta\n"
        f"• 🎥 Videolar: {session.video_count} ta\n"
        f"• 🎵 Musiqa: <b>{music_name}</b>\n\n"
        f"<i>Yana rasm yoki video yuborishingiz mumkin. "
        f"Pastdagi tugmalar orqali sozlamalarni o'zgartiring va «🎬 Videoni yaratish» tugmasini bosing!</i>"
    )

    keyboard = get_control_keyboard(
        style=session.style,
        aspect=session.aspect,
        duration=str(session.duration),
        total_count=session.total_count,
        music_choice=session.music_choice,
        has_custom_audio=(session.custom_audio is not None)
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
