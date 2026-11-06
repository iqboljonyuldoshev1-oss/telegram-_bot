from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from session_manager import ROMANTIC_TRACKS

STYLE_NAMES = {
    "ken_burns": "🎥 Kino (Ken Burns Zoom)",
    "crossfade": "🌊 Yumshoq Crossfade",
    "slide_left": "➡️ Slayd (Siljish)",
    "zoom_flash": "⚡ Dinamik Flash"
}

ASPECT_NAMES = {
    "9:16": "📱 9:16 (Reels, TikTok, Stories)",
    "16:9": "🖥 16:9 (Gorizontal / YouTube)",
    "1:1": "⏹ 1:1 (Kvadrat / Post)"
}

DURATION_NAMES = {
    "1.5": "⚡ 1.5 soniya (Tezkor)",
    "3.0": "⏳ 3.0 soniya (Standart)",
    "4.5": "🐢 4.5 soniya (Sekin)"
}

def get_music_label(music_choice: str, has_custom: bool) -> str:
    if music_choice == "custom" and has_custom:
        return "🎧 Shaxsiy musiqa"
    return ROMANTIC_TRACKS.get(music_choice, "🌹 Mayin Pianino")


def get_control_keyboard(
    style: str,
    aspect: str,
    duration: str,
    total_count: int,
    music_choice: str,
    has_custom_audio: bool
) -> InlineKeyboardMarkup:
    style_label = STYLE_NAMES.get(style, "🎥 Kino")
    aspect_label = ASPECT_NAMES.get(aspect, "📱 9:16")
    dur_label = DURATION_NAMES.get(str(duration), f"{duration}s")
    music_label = get_music_label(music_choice, has_custom_audio)

    buttons = [
        [InlineKeyboardButton(text=f"🎬 Videoni yaratish ({total_count} ta fayl)", callback_data="btn_render")],
        [InlineKeyboardButton(text=f"🎵 Musiqa: {music_label}", callback_data="menu_music")],
        [InlineKeyboardButton(text=f"🎨 Uslub: {style_label}", callback_data="menu_style")],
        [InlineKeyboardButton(text=f"📐 O'lcham: {aspect_label}", callback_data="menu_aspect")],
        [InlineKeyboardButton(text=f"⏱ Kadr vaqti: {dur_label}", callback_data="menu_duration")],
        [InlineKeyboardButton(text="🗑 Tozalash / Qayta boshlash", callback_data="btn_clear")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_music_keyboard(current_choice: str, has_custom_audio: bool) -> InlineKeyboardMarkup:
    buttons = []
    for key, name in ROMANTIC_TRACKS.items():
        mark = " ✅" if key == current_choice else ""
        buttons.append([InlineKeyboardButton(text=f"{name}{mark}", callback_data=f"set_music:{key}")])

    if has_custom_audio:
        mark = " ✅" if current_choice == "custom" else ""
        buttons.append([InlineKeyboardButton(text=f"🎧 Shaxsiy yuborilgan musiqa{mark}", callback_data="set_music:custom")])

    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_style_keyboard(selected_style: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, name in STYLE_NAMES.items():
        mark = " ✅" if key == selected_style else ""
        buttons.append([InlineKeyboardButton(text=f"{name}{mark}", callback_data=f"set_style:{key}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_aspect_keyboard(selected_aspect: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, name in ASPECT_NAMES.items():
        mark = " ✅" if key == selected_aspect else ""
        buttons.append([InlineKeyboardButton(text=f"{name}{mark}", callback_data=f"set_aspect:{key}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard(selected_duration: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, name in DURATION_NAMES.items():
        mark = " ✅" if str(key) == str(selected_duration) else ""
        buttons.append([InlineKeyboardButton(text=f"{name}{mark}", callback_data=f"set_duration:{key}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
