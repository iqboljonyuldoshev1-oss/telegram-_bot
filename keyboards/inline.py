from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    "2.5": "⏳ 2.5 soniya (Standart)",
    "4.0": "🐢 4.0 soniya (Sekin)"
}

def get_control_keyboard(style: str, aspect: str, duration: str, photo_count: int, has_audio: bool) -> InlineKeyboardMarkup:
    style_label = STYLE_NAMES.get(style, "🎥 Kino")
    aspect_label = ASPECT_NAMES.get(aspect, "📱 9:16")
    dur_label = DURATION_NAMES.get(str(duration), f"{duration}s")
    audio_icon = "🎵 Musiqa bor ✅" if has_audio else "➕ Musiqa qo'shish"

    buttons = [
        [InlineKeyboardButton(text=f"🎬 Videoni yaratish ({photo_count} ta rasm)", callback_data="btn_render")],
        [InlineKeyboardButton(text=f"🎨 Uslub: {style_label}", callback_data="menu_style")],
        [InlineKeyboardButton(text=f"📐 O'lcham: {aspect_label}", callback_data="menu_aspect")],
        [InlineKeyboardButton(text=f"⏱ Har bir rasm: {dur_label}", callback_data="menu_duration")],
        [
            InlineKeyboardButton(text=audio_icon, callback_data="menu_audio_info"),
            InlineKeyboardButton(text="🗑 Tozalash", callback_data="btn_clear")
        ]
    ]
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

