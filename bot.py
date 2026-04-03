import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import database as db
import random
import os

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB_URL = os.getenv("WEB_URL", "http://127.0.0.1:5000")

bot = telebot.TeleBot(TOKEN)

# ═══════════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════════
FIELDS = ["Computer Science", "Electrical Engineering", "Mechanical Engineering",
          "Physics", "Mathematics", "Bioengineering", "Chemistry", "Other"]

TIPS = [
    "📌 KAIST GPA talabi: min 3.0/4.0 (baholash tizimига qarab)",
    "📌 IELTS 6.5+ yoki TOEFL 90+ talab qilinadi (CS uchun 7.0+)",
    "📌 SOP da nega KAIST? — aniq professor yoki lab nomini yozing",
    "📌 Har bir hujjat apostil bilan tasdiqlangan bo'lishi shart",
    "📌 Tavsiya xatlari akademik bo'lishi kerak — professor yoki ilmiy rahbar",
    "📌 GKS stipendiyasi uchun alohida ariza: deadline aprel oxiri",
    "📌 Research experience KAIST qabul komissiyasiga muhim omil",
    "📌 Korean Certificate (TOPIK) bo'lsa — bu sizga bonus ball beradi",
    "📌 KAIST Fall 2026 qabuli: ariza topshirish muddati — 30 avgust",
    "📌 Intervyuda o'zingizning research motivatsiyangizni aniq ifodalang",
]

INTERVIEW_QUESTIONS = [
    "Why did you choose KAIST specifically over other Asian universities?",
    "Describe your most significant research experience and what you learned.",
    "Where do you see yourself 10 years after graduating from KAIST?",
    "What specific contribution will you make to KAIST's research community?",
    "Explain a complex academic problem you solved under pressure.",
    "How do you handle failure and setbacks in your academic career?",
    "What is your most ambitious long-term research goal?",
    "Why did you choose your specific field of study?",
    "How will your background benefit KAIST's diversity?",
    "What professor or lab at KAIST do you want to work with, and why?",
]

# Foydalanuvchi holati (oddiy dict, production'da Redis ishlatish tavsiya etiladi)
user_state = {}

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def main_menu(tg_id):
    """Asosiy menyu — inline tugmalar."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎯 AI Tahlil", callback_data="predict"),
        InlineKeyboardButton("✍️ SOP Yarat", callback_data="sop"),
        InlineKeyboardButton("🎤 Intervyu", callback_data="interview"),
        InlineKeyboardButton("📋 Hujjatlar", callback_data="docs"),
        InlineKeyboardButton("📅 Deadline", callback_data="deadline"),
        InlineKeyboardButton("🎓 Stipendiyalar", callback_data="scholarship"),
        InlineKeyboardButton("🤝 Hamjamiyat", callback_data="match"),
        InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        InlineKeyboardButton("🗺 Yo'l Xaritasi", callback_data="roadmap"),
        InlineKeyboardButton("💡 Kunlik Maslahat", callback_data="tip"),
    )
    markup.add(InlineKeyboardButton("🌐 Saytga Kirish", url=web_login_url(tg_id)))
    return markup

def web_login_url(tg_id):
    user = db.get_user(tg_id)
    if user and user.get('token'):
        return f"{WEB_URL}/auth?token={user['token']}"
    return WEB_URL

def profile_text(u):
    bar_len = 10
    xp_pct = int((u['xp'] / 10000) * bar_len)
    bar = "█" * xp_pct + "░" * (bar_len - xp_pct)
    return (
        f"👤 <b>{u['name']}</b>  @{u['username'] or '—'}\n"
        f"🎓 {u['university'] or '—'}  |  {u['field'] or '—'}\n"
        f"📊 GPA: <b>{u['gpa'] or '—'}</b>   🗣 IELTS: <b>{u['ielts'] or '—'}</b>\n"
        f"🔬 Tadqiqot: {u['research']}  |  🏆 Mukofot: {u['awards']}\n\n"
        f"⚡ Daraja: <b>LEVEL {u['level']}</b>\n"
        f"[{bar}] {u['xp']:,} / 10,000 XP\n"
    )

def calc_chance(u):
    score = 30
    if u['gpa'] >= 95: score += 28
    elif u['gpa'] >= 90: score += 20
    elif u['gpa'] >= 80: score += 12
    if u['ielts'] >= 7.5: score += 18
    elif u['ielts'] >= 7.0: score += 12
    elif u['ielts'] >= 6.5: score += 6
    if u['research'] >= 2: score += 12
    elif u['research'] == 1: score += 6
    if u['awards'] >= 1: score += 8
    return min(97, max(5, score))

def chance_emoji(score):
    if score >= 75: return "🟢"
    if score >= 50: return "🟡"
    return "🔴"

# ═══════════════════════════════════════════════════════════════
#  /start — RO'YXATDAN O'TISH
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    tg_id = msg.from_user.id
    name = msg.from_user.first_name or "Foydalanuvchi"
    username = msg.from_user.username or ""
    token = db.create_user(tg_id, name, username)
    user = db.get_user(tg_id)

    if user.get('gpa', 0) == 0 and not user.get('field'):
        # Yangi foydalanuvchi — ro'yxatdan o'tkazish
        bot.send_message(msg.chat.id,
            f"🚀 <b>K-HUB MASTER TREEga xush kelibsiz!</b>\n\n"
            f"Salom, <b>{name}</b>! Men sizga KAIST universitetiga qabul bo'lishda yordam beraman.\n\n"
            f"Avval bir necha savol — to'liq ma'lumot kiritsangiz, tahlil aniqroq bo'ladi.",
            parse_mode='HTML'
        )
        user_state[tg_id] = {'step': 'uni'}
        bot.send_message(msg.chat.id, "🏫 Hozir qaysi universitetda o'qiyapsiz yoki o'qigansiz?")
    else:
        bot.send_message(msg.chat.id,
            f"🎮 Xush kelibsiz, <b>{name}</b>!\n\n{profile_text(user)}",
            parse_mode='HTML', reply_markup=main_menu(tg_id)
        )

# ═══════════════════════════════════════════════════════════════
#  RO'YXATDAN O'TISH BOSQICHLARI
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.from_user.id in user_state)
def registration_step(msg):
    tg_id = msg.from_user.id
    step = user_state.get(tg_id, {}).get('step')
    text = msg.text.strip()

    if step == 'uni':
        db.update_user(tg_id, university=text)
        # Yo'nalishni tanlash uchun tugmalar
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for f in FIELDS:
            markup.add(KeyboardButton(f))
        user_state[tg_id]['step'] = 'field'
        bot.send_message(msg.chat.id, "📚 Ta'lim yo'nalishingizni tanlang:", reply_markup=markup)

    elif step == 'field':
        db.update_user(tg_id, field=text)
        user_state[tg_id]['step'] = 'gpa'
        bot.send_message(msg.chat.id,
            "📊 GPA balingiz necha? (100 ballik tizimda yozing, masalan: <b>92.5</b>)",
            parse_mode='HTML')

    elif step == 'gpa':
        try:
            gpa = float(text)
            if not 0 <= gpa <= 100: raise ValueError
            db.update_user(tg_id, gpa=gpa)
            user_state[tg_id]['step'] = 'ielts'
            bot.send_message(msg.chat.id,
                "🗣 IELTS balingiz necha? (masalan: <b>7.0</b>)\n"
                "Agar topshirmagan bo'lsangiz: <b>0</b> yozing",
                parse_mode='HTML')
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Noto'g'ri format. 0-100 orasida son kiriting:")

    elif step == 'ielts':
        try:
            ielts = float(text)
            if not 0 <= ielts <= 9: raise ValueError
            db.update_user(tg_id, ielts=ielts)
            user_state[tg_id]['step'] = 'research'
            bot.send_message(msg.chat.id,
                "🔬 Nechta ilmiy maqola yoki tadqiqot loyihasi bor? (son kiriting, masalan: <b>2</b>)",
                parse_mode='HTML')
        except ValueError:
            bot.send_message(msg.chat.id, "❌ IELTS bali 0-9 orasida bo'lishi kerak:")

    elif step == 'research':
        try:
            r = int(text)
            db.update_user(tg_id, research=r)
            user_state[tg_id]['step'] = 'awards'
            bot.send_message(msg.chat.id,
                "🏆 Olimpiada yoki musobaqa sovrindorlari soni? (masalan: <b>1</b>)",
                parse_mode='HTML')
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Butun son kiriting (0, 1, 2 ...):")

    elif step == 'awards':
        try:
            a = int(text)
            db.update_user(tg_id, awards=a)
            db.add_xp(tg_id, 500)  # Ro'yxatdan o'tganlik uchun XP
            del user_state[tg_id]
            user = db.get_user(tg_id)
            chance = calc_chance(user)
            emoji = chance_emoji(chance)

            from telebot.types import ReplyKeyboardRemove
            bot.send_message(msg.chat.id,
                f"✅ <b>Profil yaratildi!</b>\n\n{profile_text(user)}\n"
                f"{emoji} <b>Dastlabki KAIST kirish imkoniyati: {chance}%</b>\n\n"
                f"🎁 +500 XP qo'shildi!\n\n"
                f"Quyidagi menyudan foydalaning 👇",
                parse_mode='HTML',
                reply_markup=ReplyKeyboardRemove()
            )
            bot.send_message(msg.chat.id, "📡 K-Hub boshqaruv paneli:",
                             reply_markup=main_menu(tg_id))
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Butun son kiriting:")

# ═══════════════════════════════════════════════════════════════
#  ASOSIY KOMANDALAR
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=['profile'])
def cmd_profile(msg):
    user = db.get_user(msg.from_user.id)
    if not user:
        return bot.send_message(msg.chat.id, "❌ Avval /start orqali ro'yxatdan o'ting.")
    bot.send_message(msg.chat.id, profile_text(user),
                     parse_mode='HTML', reply_markup=main_menu(msg.from_user.id))

@bot.message_handler(commands=['predict'])
def cmd_predict(msg):
    user = db.get_user(msg.from_user.id)
    if not user:
        return bot.send_message(msg.chat.id, "❌ Avval /start orqali ro'yxatdan o'ting.")
    show_prediction(msg.chat.id, user)
    db.add_xp(msg.from_user.id, 200)

def show_prediction(chat_id, user):
    chance = calc_chance(user)
    emoji = chance_emoji(chance)
    strengths, weaknesses = [], []
    if user['gpa'] >= 90: strengths.append("GPA")
    else: weaknesses.append("GPA (target: 90+)")
    if user['ielts'] >= 7.0: strengths.append("IELTS")
    else: weaknesses.append("IELTS (target: 7.0+)")
    if user['research'] >= 1: strengths.append("Tadqiqot")
    else: weaknesses.append("Tadqiqot tajribasi yo'q")
    if user['awards'] >= 1: strengths.append("Mukofotlar")

    bar = int(chance / 10) * "█" + (10 - int(chance / 10)) * "░"
    text = (
        f"🎯 <b>AI KAIST KIRISH TAHLILI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} <b>Ehtimollik: {chance}%</b>\n"
        f"[{bar}]\n\n"
        f"✅ <b>Kuchli tomonlar:</b>\n" +
        ("\n".join(f"  • {s}" for s in strengths) or "  • (hali yo'q)") +
        f"\n\n⚠️ <b>Yaxshilash kerak:</b>\n" +
        ("\n".join(f"  • {w}" for w in weaknesses) or "  • Barchasi yaxshi!") +
        f"\n\n💡 <i>Ma'lumotlaringizni yangilash uchun /update yozing</i>"
    )
    bot.send_message(chat_id, text, parse_mode='HTML')

@bot.message_handler(commands=['sop'])
def cmd_sop(msg):
    user = db.get_user(msg.from_user.id)
    if not user:
        return bot.send_message(msg.chat.id, "❌ Avval /start orqali ro'yxatdan o'ting.")
    u = user
    sop = (
        f"📄 <b>STATEMENT OF PURPOSE</b>\n"
        f"<i>Generated by K-Hub AI</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"My name is <b>{u['name']}</b>, and I am applying to KAIST's "
        f"<b>{u['field']}</b> program with a deep passion for advancing "
        f"knowledge in my field. Throughout my academic journey at "
        f"<b>{u['university']}</b>, I have maintained a GPA of <b>{u['gpa']}</b> "
        f"and achieved an IELTS score of <b>{u['ielts']}</b>, demonstrating "
        f"both academic excellence and English proficiency.\n\n"
        f"I have engaged in <b>{u['research']}</b> research project(s) and "
        f"earned <b>{u['awards']}</b> award(s), which reflect my commitment "
        f"to academic and professional growth beyond the classroom.\n\n"
        f"KAIST represents the pinnacle of scientific innovation in Asia. "
        f"Its culture of rigorous, interdisciplinary research aligns perfectly "
        f"with my ambition. I am confident that my background uniquely "
        f"positions me to contribute meaningfully to KAIST's research community "
        f"and to grow as a researcher under the guidance of its world-class faculty.\n\n"
        f"I am fully committed to making the most of this opportunity and "
        f"to contributing to the advancement of <b>{u['field']}</b>.\n\n"
        f"<i>— {u['name']}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 To'liq versiya va tahrirlash uchun saytga kiring 🌐"
    )
    bot.send_message(msg.chat.id, sop, parse_mode='HTML')
    db.add_xp(msg.from_user.id, 300)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🌐 Saytda Ko'rish & Tahrirlash", url=web_login_url(msg.from_user.id)))
    bot.send_message(msg.chat.id, "SOP tayyor! Saytda batafsil tahrirlash imkoniyati mavjud:", reply_markup=markup)

@bot.message_handler(commands=['interview'])
def cmd_interview(msg):
    q = random.choice(INTERVIEW_QUESTIONS)
    user_state[msg.from_user.id] = {'step': 'interview_answer', 'question': q}
    bot.send_message(msg.chat.id,
        f"🎤 <b>AI INTERVYU SIMULYATORI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❓ <b>Savol:</b>\n<i>{q}</i>\n\n"
        f"Javobingizni yozing (ingliz yoki o'zbek tilida):",
        parse_mode='HTML')

@bot.message_handler(commands=['deadline'])
def cmd_deadline(msg):
    from datetime import datetime
    target = datetime(2026, 8, 30, 23, 59, 59)
    now = datetime.now()
    diff = target - now
    days = diff.days
    hours = diff.seconds // 3600
    mins = (diff.seconds // 60) % 60
    bot.send_message(msg.chat.id,
        f"📅 <b>KAIST FALL 2026 — DEADLINE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ Qolgan vaqt:\n"
        f"   📆 <b>{days}</b> kun\n"
        f"   🕐 <b>{hours}</b> soat\n"
        f"   ⏱ <b>{mins}</b> daqiqa\n\n"
        f"🗓 Ariza topshirish: <b>30 Avgust 2026</b>\n"
        f"🗓 GKS Scholarship: <b>30 Aprel 2026</b>\n\n"
        f"⚡ Hujjatlar tayyor? /docs buyrug'i bilan tekshiring!",
        parse_mode='HTML')

@bot.message_handler(commands=['docs'])
def cmd_docs(msg):
    tg_id = msg.from_user.id
    user = db.get_user(tg_id)
    if not user:
        return bot.send_message(msg.chat.id, "❌ Avval /start orqali ro'yxatdan o'ting.")
    docs = db.get_docs(tg_id)
    markup = InlineKeyboardMarkup(row_width=1)
    done = 0
    for d in docs:
        if d['checked']:
            done += 1
            markup.add(InlineKeyboardButton(f"✅ {d['doc_name']}", callback_data=f"doc_skip_{d['doc_name']}"))
        else:
            markup.add(InlineKeyboardButton(f"☐  {d['doc_name']}", callback_data=f"doc_{d['doc_name']}"))
    pct = int((done / len(docs)) * 100) if docs else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    bot.send_message(msg.chat.id,
        f"📋 <b>HUJJATLAR NAZORATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"[{bar}] {pct}% tayyor ({done}/{len(docs)})\n\n"
        f"Belgilash uchun hujjat nomiga bosing 👇",
        parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['scholarship'])
def cmd_scholarship(msg):
    user = db.get_user(msg.from_user.id)
    chance = calc_chance(user) if user else 0
    bot.send_message(msg.chat.id,
        f"🎓 <b>STIPENDIYALAR & GRANTLAR</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🥇 <b>GKS-G (Global Korea Scholarship)</b>\n"
        f"   • 100% o'qish haqi + yashash xarajati + aviabilet\n"
        f"   • Deadline: 30 Aprel 2026\n"
        f"   • {'✅ Profil mos' if chance >= 60 else '⚠️ Profilni kuchaytiring'}\n\n"
        f"🥈 <b>KAIST Research Excellence Award</b>\n"
        f"   • $12,000/yil tadqiqot stipendiyasi\n"
        f"   • Talab: 2+ maqola yoki loyiha\n"
        f"   • {'✅ Mos' if (user and user.get('research',0) >= 2) else '⚠️ Tadqiqot kerak'}\n\n"
        f"🥉 <b>Samsung Hope Scholarship</b>\n"
        f"   • Rivojlanayotgan davlatlar uchun qisman stipendiya\n"
        f"   • Deadline: Iyun 2026\n\n"
        f"🔗 <b>Korea Foundation Fellowship</b>\n"
        f"   • Til va madaniyat integratsiya granti\n\n"
        f"💡 Barcha stipendiyalar: kaist.ac.kr/scholarship",
        parse_mode='HTML')
    db.add_xp(msg.from_user.id, 100)

@bot.message_handler(commands=['match'])
def cmd_match(msg):
    bot.send_message(msg.chat.id,
        f"🤝 <b>HAMJAMIYAT TARMOG'I</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🇺🇿 @Aziz_99 — CS / AI — GPA 96% — Match: 92%\n"
        f"🇺🇿 @Kamil_2025 — EE — GPA 91% — Match: 81%\n"
        f"🇰🇿 @Aliya_KZ — Physics — GPA 94% — Match: 78%\n"
        f"🇷🇺 @DmitriT — Physics — GPA 98% — Match: 76%\n\n"
        f"📌 Profilingiz to'liq bo'lsa ko'proq moslik topiladi\n"
        f"🌐 To'liq hamjamiyat saytda: /start → saytga kirish",
        parse_mode='HTML')

@bot.message_handler(commands=['tip'])
def cmd_tip(msg):
    tip = random.choice(TIPS)
    bot.send_message(msg.chat.id,
        f"💡 <b>KUNLIK KAIST MASLAHATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{tip}\n\n"
        f"<i>Ertaga yangi maslahat! Boshqasi uchun /tip yozing</i>",
        parse_mode='HTML')
    db.add_xp(msg.from_user.id, 50)

@bot.message_handler(commands=['stats'])
def cmd_stats(msg):
    user = db.get_user(msg.from_user.id)
    if not user:
        return bot.send_message(msg.chat.id, "❌ Avval /start orqali ro'yxatdan o'ting.")
    docs = db.get_docs(msg.from_user.id)
    docs_done = sum(1 for d in docs if d['checked'])
    chance = calc_chance(user)
    emoji = chance_emoji(chance)
    bar_len = 10
    xp_pct = int((user['xp'] / 10000) * bar_len)
    xpbar = "█" * xp_pct + "░" * (bar_len - xp_pct)
    bot.send_message(msg.chat.id,
        f"📊 <b>KAIST TAYYORLIK STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {user['name']} | Level {user['level']}\n"
        f"[{xpbar}] {user['xp']:,}/10,000 XP\n\n"
        f"{emoji} Kirish imkoniyati: <b>{chance}%</b>\n"
        f"📋 Hujjatlar: <b>{docs_done}/{len(docs)}</b>\n"
        f"🎓 Daraja: {user['field'] or '—'}\n"
        f"🏫 Universitet: {user['university'] or '—'}\n"
        f"📊 GPA: {user['gpa']}  |  🗣 IELTS: {user['ielts']}\n"
        f"🔬 Tadqiqot: {user['research']}  |  🏆 Mukofot: {user['awards']}",
        parse_mode='HTML', reply_markup=main_menu(msg.from_user.id))

@bot.message_handler(commands=['roadmap'])
def cmd_roadmap(msg):
    bot.send_message(msg.chat.id,
        f"🗺 <b>KAIST KIRISH YO'L XARITASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ 1. Transkript va diplom olish\n"
        f"✅ 2. Apostil tasdiqlash (4-6 hafta)\n"
        f"🔵 3. IELTS topshirish (target: 7.0+) ← Hozir\n"
        f"⬜ 4. SOP yozish va qayta ko'rib chiqish\n"
        f"⬜ 5. Tavsiya xatlari to'plash\n"
        f"⬜ 6. Ariza topshirish (Avgust 30)\n\n"
        f"📌 Har bir bosqichni /docs orqali belgilang\n"
        f"💡 Savol bo'lsa /tip yozing",
        parse_mode='HTML')

@bot.message_handler(commands=['update'])
def cmd_update(msg):
    user_state[msg.from_user.id] = {'step': 'uni'}
    bot.send_message(msg.chat.id,
        "🔄 <b>Profilni yangilash</b>\n\nUniversitet nomini kiriting:",
        parse_mode='HTML')

@bot.message_handler(commands=['help'])
def cmd_help(msg):
    bot.send_message(msg.chat.id,
        f"📖 <b>K-HUB BOT — BARCHA KOMANDALAR</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"/start — Bosh menyu / Ro'yxatdan o'tish\n"
        f"/profile — Profilingizni ko'rish\n"
        f"/predict — AI kirish imkoniyati tahlili\n"
        f"/sop — SOP (esse) generatsiya\n"
        f"/interview — Intervyu savoli va AI feedback\n"
        f"/roadmap — Qadamba-qadam yo'l xaritasi\n"
        f"/deadline — Qabuulgacha qolgan vaqt\n"
        f"/docs — Hujjatlar cheklisti\n"
        f"/scholarship — Stipendiyalar ro'yxati\n"
        f"/match — Hamjamiyat va mosliklar\n"
        f"/tip — Kunlik KAIST maslahati\n"
        f"/stats — To'liq statistika\n"
        f"/update — Profilni yangilash\n"
        f"/help — Ushbu ro'yxat\n\n"
        f"🌐 Sayt: /start → \"Saytga Kirish\" tugmasi",
        parse_mode='HTML')

# ═══════════════════════════════════════════════════════════════
#  CALLBACK HANDLERS (Inline tugmalar)
# ═══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith('doc_'))
def cb_doc(call):
    tg_id = call.from_user.id
    if call.data.startswith('doc_skip_'):
        bot.answer_callback_query(call.id, "Bu hujjat allaqachon belgilangan ✅")
        return
    doc_name = call.data[4:]
    db.check_doc(tg_id, doc_name)
    db.add_xp(tg_id, 150)
    bot.answer_callback_query(call.id, f"✅ Belgilandi! +150 XP")
    # Yangi holatni ko'rsatish
    cmd_docs_cb(call.message, tg_id)

def cmd_docs_cb(msg, tg_id):
    docs = db.get_docs(tg_id)
    markup = InlineKeyboardMarkup(row_width=1)
    done = 0
    for d in docs:
        if d['checked']:
            done += 1
            markup.add(InlineKeyboardButton(f"✅ {d['doc_name']}", callback_data=f"doc_skip_{d['doc_name']}"))
        else:
            markup.add(InlineKeyboardButton(f"☐  {d['doc_name']}", callback_data=f"doc_{d['doc_name']}"))
    pct = int((done / len(docs)) * 100) if docs else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    bot.edit_message_text(
        f"📋 <b>HUJJATLAR NAZORATI</b>\n[{bar}] {pct}% tayyor ({done}/{len(docs)})\n\n👇",
        msg.chat.id, msg.message_id, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb_menu(call):
    tg_id = call.from_user.id
    d = call.data
    bot.answer_callback_query(call.id)
    if d == 'predict':
        user = db.get_user(tg_id)
        if user: show_prediction(call.message.chat.id, user); db.add_xp(tg_id, 200)
    elif d == 'sop': cmd_sop(call.message)
    elif d == 'interview': cmd_interview(call.message)
    elif d == 'docs': cmd_docs(call.message)
    elif d == 'deadline': cmd_deadline(call.message)
    elif d == 'scholarship': cmd_scholarship(call.message)
    elif d == 'match': cmd_match(call.message)
    elif d == 'stats': cmd_stats(call.message)
    elif d == 'roadmap': cmd_roadmap(call.message)
    elif d == 'tip': cmd_tip(call.message)

# ═══════════════════════════════════════════════════════════════
#  INTERVYU JAVOBI
# ═══════════════════════════════════════════════════════════════
def handle_interview_answer(msg, tg_id):
    state = user_state.get(tg_id, {})
    question = state.get('question', '')
    answer = msg.text.strip()
    words = len(answer.split())
    score = min(100, 50 + words * 2 + random.randint(-10, 15))
    emoji = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")
    feedback_hints = {
        "low":  "Javobingiz juda qisqa. Ko'proq detal qo'shing va konkret misollar keltiring.",
        "mid":  "Javob o'rtacha. Motivatsiyangizni aniqroq ifodalashga harakat qiling.",
        "high": "Yaxshi javob! KAIST intervyusida bunday aniqlik va ishonch zarur.",
    }
    level = "high" if score >= 75 else ("mid" if score >= 50 else "low")
    db.log_interview(tg_id, question, answer, score)
    db.add_xp(tg_id, 250)
    del user_state[tg_id]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Yana bir savol", callback_data="interview"))
    bot.send_message(msg.chat.id,
        f"🎤 <b>AI FEEDBACK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} <b>Ball: {score}/100</b>\n\n"
        f"💬 {feedback_hints[level]}\n\n"
        f"📊 So'zlar soni: {words}\n"
        f"⚡ +250 XP qo'shildi!",
        parse_mode='HTML', reply_markup=markup)

# ═══════════════════════════════════════════════════════════════
#  MATN XABARLARNI ROUTING
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    tg_id = msg.from_user.id
    state = user_state.get(tg_id, {})
    if state.get('step') == 'interview_answer':
        handle_interview_answer(msg, tg_id)
    else:
        bot.send_message(msg.chat.id,
            "ℹ️ Menyu uchun /help yozing yoki pastdagi tugmalardan foydalaning.",
            reply_markup=main_menu(tg_id))

# ═══════════════════════════════════════════════════════════════
#  ISHGA TUSHIRISH
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("🤖 K-Hub Telegram Bot ishga tushdi...")
    print(f"🔗 Bot: @{bot.get_me().username}")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
