# 🎬 Telegram Photo-to-Video Maker Bot (Asl sifatli video montaj boti)

Ushbu Telegram bot foydalanuvchilar yuborgan bir nechta fotosuratlardan yuqori sifatli, professional va chiroyli videoroliklar yaratib beradi.

---

## 🌟 Asosiy xususiyatlar

1. **Sun'iy intellekt buzilishlarisiz (No AI Hallucinations):**
   - Ko'pgina AI video generatorlar rasmdagi odamlarning yuzini, qo'llarini yoki fonini g'alati qilib o'zgartirib yuboradi.
   - Bu bot esa **100% original rasmlarning asl sifatini, aniqligini va tiniqligini** saqlagan holda zamonaviy kinematografik video montaj qilib beradi!

2. **Chiroyli o'tish effektlari (Transitions):**
   - 🎥 **Kino (Ken Burns Zoom):** Sekin va ravon yaqinlashish/uzoqlashish + fotosuratlar oralig'ida crossfade (hujjatli film va to'y roliklari uslubida).
   - 🌊 **Yumshoq Crossfade:** Bir fotosuratdan ikkinchisiga nafis erish orqali o'tish.
   - ➡️ **Slayd (Yon tomonga surilish):** Smoothstep silliqligi bilan suriluvchi dinamik kadrlar.
   - ⚡ **Dinamik Flash:** Ritmik oq chaqnash va tezkor o'tish (zamonaviy reels va ritmik videolar uchun).

3. **Format va o'lchamlar (Aspect Ratios):**
   - 📱 **9:16 (720x1280):** Instagram Reels, TikTok, YouTube Shorts, Telegram Stories uchun.
   - 🖥 **16:9 (1280x720):** YouTube, kompyuter va televizorlar uchun gorizontal format.
   - ⏹ **1:1 (1080x1080):** Instagram postlar va kvadrat format.

4. **Professional xiralashtirilgan fon (Blurred Background):**
   - Agar foydalanuvchi gorizontal rasmni vertikal (9:16) formatda yasamoqchi bo'lsa, qora chiziqlar o'rniga orqa fon xuddi shu rasmning xiralashtirilgan va qorong'ulashtirilgan ko'rinishi bilan to'ldiriladi. Bu esa videoni nihoyatda professional ko'rsatadi!

5. **Musiqa va audio qo'shish:**
   - Foydalanuvchi istalgan MP3 qo'shiq yoki ovozli xabar yuborsa, bot uni avtomatik ravishda video bilan sinxronlashtiradi va oxirida yumshoq ovoz so'nishi (audio fade-out) bilan birlashtiradi.

---

## 📁 Loyiha tuzilishi

```text
bot/
├── config.py             # Bot sozlamalari va papkalar
├── session_manager.py    # Foydalanuvchi sessiyalari va yuklangan rasmlar
├── video_maker.py        # OpenCV + FFmpeg video montaj mexanizmi
├── keyboards/
│   ├── __init__.py
│   └── inline.py         # Interaktiv boshqaruv paneli tugmalari
├── handlers/
│   ├── __init__.py
│   ├── start.py          # /start, /help, /reset komandalari
│   ├── media.py          # Rasmlar va musiqalarni qabul qilish
│   └── video.py          # Video yaratish va sozlamalarni o'zgartirish
├── main.py               # Asosiy ishga tushirish fayli
├── requirements.txt      # Kerakli Python kutubxonalari
├── .env                  # Bot tokeni
└── README.md             # Qo'llanma
```

---

## 🚀 Ishga tushirish

### 1. Telegramdan Bot Token olish:
1. Telegramda [@BotFather](https://t.me/BotFather) botini oching.
2. `/newbot` buyrug'ini yuboring va ko'rsatmalarga amal qilib botingizga nom bering.
3. BotFather sizga bergan `API Token`ni nusxalab oling.

### 2. .env faylini sozlash:
`C:\Users\user\Desktop\bot\.env` faylini oching va tokenni yozing:
```env
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 3. Kutubxonalarni o'rnatish (agar o'rnatilmagan bo'lsa):
```powershell
pip install -r requirements.txt
```

### 4. Botni ishga tushirish:
```powershell
python main.py
```

Endi botingizga o'tib `/start` ni bosing va rasmlarni yuboring! 🎉

