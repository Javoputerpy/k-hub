import os, sys, threading, uuid, datetime, json, requests, time, subprocess
from flask import Flask, render_template, request, session, redirect, jsonify, send_file
from dotenv import load_dotenv
import database as db

load_dotenv()

# ── BOT INTEGRATION (Run Bot along with Web) ──
if os.environ.get('START_BOT', 'true').lower() == 'true':
    # We use a simple check to avoid starting the bot multiple times in dev mode
    if not os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("🚀 Launching Telegram Bot...")
        subprocess.Popen([sys.executable, "bot.py"])

# Safe encoding for Windows
if sys.stdout.encoding != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except: pass

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── I18N (SERVER SIDE TRANSLATIONS) ──
T = {
    'uz': {
        'login_btn': 'KIRISH', 'welcome': 'Xush kelibsiz',
        'tab_skills': 'ASOSIY', 'tab_predictor': 'AI TAHLIL', 'tab_sop': 'SOP LAB',
        'tab_email': 'EMAILER', 'tab_interview': 'INTERVYU', 'tab_research': 'TADQIQOT',
        'tab_roadmap': "XARITA", 'tab_network': 'TARMOQ', 'tab_scholarships': 'GRANTLAR',
        'tab_portfolio': 'PORTFOLIO', 'tab_labs': 'LABLAR', 'tab_stats': 'STATISTIKA',
        'tab_docs': 'HUJJATLAR', 'tab_admin': 'ADMIN', 'tab_about': 'BIZ HAQIMIZDA', 'tab_settings': 'SOZLAMALAR',
        'btn_connect': 'BOG\'LANISH', 'btn_generate': 'YARATISH', 'btn_search': 'QIDIRISH', 'btn_apply': 'TOPSHIRISH',
        'net_find': 'Hamjamiyatdan do\'stlar toping', 'email_prof': 'Professorga xat yozish', 'res_labs': 'KAIST Laboratoriyalari',
        'dash_welcome': 'K-Hubga xush kelibsiz', 'dash_desc': 'KAISTga tayyorgarlik uchun yakuniy dashboard.',
        'dash_stat': 'Tezkor Statistika', 'st_gpa': 'GPA Ko\'rsatkichi', 'st_ielts': 'IELTS Bali', 'st_research': 'Ilmiy ishlar',
        'adm_prob': 'Qabul Ehtimoli', 'acad_str': 'Akademik Kuch', 'port_div': 'Portfolio Rang-barangligi', 'comp_read': 'Hujjatlar Tayyorgarligi', 'bad_unlock': 'Yutilgan Nishonlar',
        'sop_arch': 'SOP Arxitektori', 'sop_draft': 'AI BILAN YOZISH', 'sop_struct': 'Tavsiya etilgan tuzilma', 'sop_step1': 'Kirish', 'sop_step1_d': 'KAISTga motivatsiya',
        'int_sim': 'Intervyu Simulyatori', 'int_start': 'MASHQLARNI BOSHLASH', 'pred_title': 'AI Qabul Predictori', 'pred_analyze': 'EHTIMOLNI HISOBLASH',
        'int_prep': 'Tayyorgarlik To\'plami', 'int_tips': 'Muhim Maslahatlar', 'int_submit': 'TAHLILGA YUBORISH', 'int_placeholder': 'Klaviatura orqali javob bering...',
        'sch_desc': 'KAIST xalqaro talabalari uchun mavjud bo\'lgan grantlar.', 'port_add': 'YANGI QO\'SHISH', 'set_account': 'Profil Sozlamalari',
        'road_title': 'Qabul Yo\'l Xaritasi', 'road_desc': 'KAISTga tomon shaxsiy sayohatingiz.', 'mile_done': 'Muvaffaqiyatli yakunlandi', 'mile_prog': 'Jarayonda',
        'port_desc': 'Loyihalaringiz va sertifikatlaringizni KAISTga ko\'rsating.', 'port_new': 'YANGI YUKLASH', 'port_share': 'CV ULASHISH',
        'doc_comp': 'Akademik Talablar', 'doc_score': 'TAYYORGARLIK DARAJASI', 'doc_pass': 'Passport nusxasi', 'doc_trans': 'Attestat/Transkript', 'doc_rec': 'Tavsiyanoma', 'doc_sop': 'Insho (SOP)',
        'abu_title': 'TALABALAR POTENSIALINI OCHISH', 'abu_ai': 'AI TAHLIL', 'abu_cv': 'SMART CV', 'abu_mock': 'MOCK LAB', 'abu_road': 'YO\'L XARITASI',
        'set_title': 'Sozalamar', 'set_photo': 'PROFIL RASMI', 'set_identity': 'SHAXSIY MA\'LUMOTLAR', 'set_pasp': 'PASSPORT SKANER', 'set_sync': 'YANGILASH VA SINXRONIZATSIYA',
        'pub_visit': 'Tashrif buyuruvchi', 'pub_gen': 'PDF YUKLASH', 'pub_ver': 'TASDIQLANGAN ID', 'pub_art': 'Tasdiqlangan Akademik Hujjatlar',
        'labs_desc': 'Xalqaro talabalarni qabul qilayotgan faol KAIST laboratorivlarini kashf eting.', 'adm_login': 'ADMIN KIRISH', 'adm_user': 'Foydalanuvchi nomi', 'adm_pw': 'Parol',
        'adm_act': 'FAOLLIK', 'adm_ver': 'TASDIQLANGAN', 'adm_bc': 'XABAR YUBORISH', 'adm_send': 'HAMMAGA YUBORISH',
        'sim_title': 'Intervyu Simulyatori', 'sim_hint': 'Klaviatura orqali javob bering...', 'sim_start': 'MASHQLARNI BOSHLASH',
        'port_share': 'CV ULASHISH', 'port_new': 'YANGI YUKLASH', 'port_desc': 'Loyihalaringiz va sertifikatlaringizni KAISTga ko\'rsating.',
        'days': 'Kun', 'hours': 'Soat', 'minutes': 'Daqiqa', 'seconds': 'Soniya',
        'mo': 'OY', 'd': 'KUN', 'h': 'S', 'm': 'D', 's': 'SN',
        'abu_kaist_title': 'KAIST: Osiyo MITi',
        'abu_kaist_desc': 'KAIST (Korea Advanced Institute of Science and Technology) Janubiy Koreyaning birinchi tadqiqotga yo\'naltirilgan ilm-fan va muhandislik instituti hisoblanadi.',
        'abu_ranking': 'Jahon Reytingi', 'abu_ranking_desc': 'QS World University Rankings bo\'yicha dunyoda kuchli 40 talikda, Osiyoda esa muhandislik bo\'yicha top 5 talikda.',
        'abu_research': 'Tadqiqot Quvvati', 'abu_research_desc': 'Yillik tadqiqot byudjeti 600 mln dollardan ortiq. Minglab patentlar va startaplar markazi.',
        'abu_global': 'Global Jamiyat', 'abu_global_desc': '90 dan ortiq davlatdan kelgan xalqaro talabalar. Barcha darslar ingliz tilida olib boriladi.',
        'dash_checklist': 'Qabul Check-listi', 'dash_quick': 'Tezkor Amallar', 'dash_advisor': 'AI Maslahatchi',
        'dash_tip': 'Sizning bugungi maslahatingiz: ',
        'dash_passport_warn': 'Pasport yuklanmagan yoki tekshirilmagan.',
        'dash_sop_ready': 'SOP Lab orqali birinchi qoralama tayyor!',
        'dash_stats_summary': 'Sizning umumiy tayyorgarlik darajangiz: ',
        'tab_blog': 'BLOG', 'tab_courses': 'KURSLAR', 'btn_learn': 'O\'RGANISH', 'btn_read': 'O\'QISH',
        'ai_tutor': 'AI Ustoz', 'lesson_chat': 'Dars bo\'yicha savollaringizni bering...'
    },
    'en': {
        'login_btn': 'LOGIN', 'welcome': 'Welcome',
        'tab_skills': 'DASHBOARD', 'tab_predictor': 'PREDICTOR', 'tab_sop': 'SOP LAB',
        'tab_email': 'EMAILER', 'tab_interview': 'INTERVIEW', 'tab_research': 'RESEARCH',
        'tab_roadmap': 'ROADMAP', 'tab_network': 'NETWORK', 'tab_scholarships': 'GRANTS',
        'tab_portfolio': 'PORTFOLIO', 'tab_labs': 'LABS', 'tab_stats': 'STATS',
        'tab_docs': 'DOCUMENTS', 'tab_admin': 'ADMIN', 'tab_about': 'ABOUT', 'tab_settings': 'SETTINGS',
        'btn_connect': 'CONNECT', 'btn_generate': 'GENERATE', 'btn_search': 'SEARCH', 'btn_apply': 'APPLY',
        'net_find': 'Find peers in community', 'email_prof': 'Academic Emailer', 'res_labs': 'KAIST Research Labs',
        'dash_welcome': 'Welcome to K-Hub', 'dash_desc': 'Your ultimate KAIST preparation dashboard.',
        'dash_stat': 'Quick Stats', 'st_gpa': 'Cumulative GPA', 'st_ielts': 'IELTS Band', 'st_research': 'Research Papers',
        'adm_prob': 'Admission Probability', 'acad_str': 'Academic Strength', 'port_div': 'Portfolio Diversity', 'comp_read': 'Compliance Readiness', 'bad_unlock': 'Unlocked Badges',
        'sop_arch': 'SOP Architect', 'sop_draft': 'DRAFT WITH AI', 'sop_struct': 'Recommended Structure', 'sop_step1': 'Introduction', 'sop_step1_d': 'Motivation for KAIST',
        'int_sim': 'Interview Simulator', 'int_start': 'START MOCK INTERVIEW', 'pred_title': 'AI Admission Predictor', 'pred_analyze': 'ANALYZE MY CHANCES',
        'int_prep': 'Preparation Toolkit', 'int_tips': 'High-Yield Tips', 'int_submit': 'SUBMIT TO ANALYST', 'int_placeholder': 'Speak through your keyboard...',
        'sch_desc': 'Explore premium scholarships available for KAIST international students.', 'port_add': 'ADD NEW ITEM', 'set_account': 'Account Settings',
        'road_title': 'Admission Roadmap', 'road_desc': 'Your personalized journey towards KAIST.', 'mile_done': 'Milestone Achieved', 'mile_prog': 'In Progress',
        'port_desc': 'Showcase your projects and certificates to KAIST.', 'port_new': 'NEW UPLOAD', 'port_share': 'SHARE PUBLIC CV',
        'doc_comp': 'Academic Compliance', 'doc_score': 'COMPLIANCE SCORE', 'doc_pass': 'Passport Copy', 'doc_trans': 'Transcript', 'doc_rec': 'Recommendation', 'doc_sop': 'Statement of Purpose',
        'abu_title': 'UNLEASHING STUDENT POTENTIAL', 'abu_ai': 'AI ANALYSIS', 'abu_cv': 'SMART CV', 'abu_mock': 'MOCK LAB', 'abu_road': 'ROADMAP',
        'set_title': 'Settings', 'set_photo': 'PROFILE PHOTO', 'set_identity': 'PROFILE IDENTITY', 'set_pasp': 'PASSPORT SCANNER', 'set_sync': 'UPDATE & SYNC',
        'pub_visit': 'Visitor', 'pub_gen': 'GENERATE PDF', 'pub_ver': 'VERIFIED ID', 'pub_art': 'Verified Academic Artifacts',
        'labs_desc': 'Discover active KAIST laboratories actively recruiting international graduate students.', 'adm_login': 'ADMIN LOGIN', 'adm_user': 'Username', 'adm_pw': 'Password',
        'adm_act': 'ACTIVE STUDENTS', 'adm_ver': 'VERIFIED ITEMS', 'adm_bc': 'GLOBAL BROADCAST', 'adm_send': 'SEND TO ALL',
        'sim_title': 'Interview Simulator', 'sim_hint': 'Speak through your keyboard...', 'sim_start': 'START MOCK INTERVIEW',
        'port_share': 'SHARE PUBLIC CV', 'port_new': 'NEW UPLOAD', 'port_desc': 'Showcase your projects and certificates to KAIST.',
        'days': 'Day', 'hours': 'Hour', 'minutes': 'Min', 'seconds': 'Sec',
        'mo': 'MO', 'd': 'D', 'h': 'H', 'm': 'M', 's': 'S',
        'abu_kaist_title': 'KAIST: The MIT of Asia',
        'abu_kaist_desc': 'KAIST is Korea\'s first and top research-oriented science and engineering institution, founded in 1971.',
        'abu_ranking': 'World Ranking', 'abu_ranking_desc': 'Consistently ranked in the Global Top 40 (QS) and Top 5 in Asia for Engineering & Technology.',
        'abu_research': 'Research Powerhouse', 'abu_research_desc': 'Over $600M annual research budget. A hub for breakthrough patents and tech startups.',
        'abu_global': 'Global Hub', 'abu_global_desc': 'Diverse student body from 90+ countries. 100% of major classes are conducted in English.',
        'dash_checklist': 'Admission Checklist', 'dash_quick': 'Quick Actions', 'dash_advisor': 'AI Advisor',
        'dash_tip': 'Your tip for today: ',
        'dash_passport_warn': 'Passport not uploaded or verified.',
        'dash_sop_ready': 'First draft is ready via SOP Lab!',
        'dash_stats_summary': 'Your overall preparation level: ',
        'tab_blog': 'BLOG', 'tab_courses': 'COURSES', 'btn_learn': 'LEARN', 'btn_read': 'READ',
        'ai_tutor': 'AI Tutor', 'lesson_chat': 'Ask your questions about this lesson...'
    },
    'kr': {
        'login_btn': '로그인', 'welcome': '환영합니다',
        'tab_skills': '대시보드', 'tab_predictor': 'AI 예측', 'tab_sop': 'SOP 작성',
        'tab_email': '이메일', 'tab_interview': '모의면접', 'tab_research': '논문요약',
        'tab_roadmap': '로드맵', 'tab_network': '네트워크', 'tab_scholarships': '장학금',
        'tab_portfolio': '포트폴리오', 'tab_labs': '연구실', 'tab_stats': '통계',
        'tab_docs': '필수서류', 'tab_admin': '관리자', 'tab_about': '소개', 'tab_settings': '설정',
        'btn_connect': '연결하기', 'btn_generate': '생성하기', 'btn_search': '검색', 'btn_apply': '지원하기',
        'net_find': '커뮤니티에서 동료 찾기', 'email_prof': '교수님 메일 작성', 'res_labs': '카이스트 연구실',
        'dash_welcome': 'K-Hub에 오신 것을 환영합니다', 'dash_desc': '카이스트 준비를 위한 대시보드입니다.',
        'dash_stat': '퀵 통계', 'st_gpa': '평점 (GPA)', 'st_ielts': '아이엘츠', 'st_research': '연구 논문',
        'adm_prob': '합격 가능성', 'acad_str': '학업 역량', 'port_div': '포트폴리오 다양성', 'comp_read': '서류 준비도', 'bad_unlock': '획득한 뱃지',
        'sop_arch': 'SOP 아키텍트', 'sop_draft': 'AI 초안 작성', 'sop_struct': '추천 구조', 'sop_step1': '서론', 'sop_step1_d': '카이스트 지원 동기',
        'int_sim': '면접 시뮬레이터', 'int_start': '모의 면접 시작', 'pred_title': 'AI 합격 예측기', 'pred_analyze': '합격 확률 분석',
        'int_prep': '면접 준비 도구', 'int_tips': '핵심 팁', 'int_submit': '분석 제출하기', 'int_placeholder': '키보드로 답변을 입력하세요...',
        'sch_desc': '카이스트 외국인 학생을 위한 장학금을 확인하세요.', 'port_add': '새 항목 추가', 'set_account': '계정 설정',
        'road_title': '입학 로드맵', 'road_desc': '카이스트를 향한 개인화된 여정입니다.', 'mile_done': '마일스톤 달성', 'mile_prog': '진행 중',
        'port_desc': '프로젝트와 수료증을 카이스트에 보여주세요.', 'port_new': '신규 업로드', 'port_share': '공개 CV 공유',
        'doc_comp': '학업 규정 준수', 'doc_score': '준수 점수', 'doc_pass': '여권 사본', 'doc_trans': '성적 증명서', 'doc_rec': '추천서', 'doc_sop': '자기소개서',
        'abu_title': '학생의 잠재력을 일깨우다', 'abu_ai': 'AI 분석', 'abu_cv': '스마트 CV', 'abu_mock': '모의 랩', 'abu_road': '로드맵',
        'set_title': '설정', 'set_photo': '프로필 사진', 'set_identity': '프로필 정보', 'set_pasp': '여권 스캐너', 'set_sync': '업데이트 및 동기화',
        'pub_visit': '방문자', 'pub_gen': 'PDF 생성', 'pub_ver': '인증된 ID', 'pub_art': '인증된 학업 결과물',
        'labs_desc': '외국인 대학원생을 모집 중인 카이스트 연구실을 확인하세요.', 'adm_login': '관리자 로그인', 'adm_user': '사용자 이름', 'adm_pw': '비밀번호',
        'adm_act': '활성 학생', 'adm_ver': '인증된 항목', 'adm_bc': '전체 공지', 'adm_send': '모두에게 전송',
        'sim_title': '면접 시뮬레이터', 'sim_hint': '키보드로 답변을 입력하세요...', 'sim_start': '모의 면접 시작',
        'port_share': '공개 CV 공유', 'port_new': '신규 업로드', 'port_desc': '프로젝트와 수료증을 카이스트에 보여주세요.',
        'days': '일', 'hours': '시간', 'minutes': '분', 'seconds': '초',
        'mo': '월', 'd': '일', 'h': '시', 'm': '분', 's': '초',
        'abu_kaist_title': 'KAIST: 아시아의 MIT',
        'abu_kaist_desc': 'KAIST는 1971년에 설립된 대한민국 최초이자 최고의 연구 중심 과학 기술 대학입니다.',
        'abu_ranking': '세계 랭킹', 'abu_ranking_desc': 'QS 세계 대학 랭킹 40위권, 아시아 공학 및 기술 분야 TOP 5를 유지하고 있습니다.',
        'abu_research': '연구 역량', 'abu_research_desc': '연간 연구 예산 6,000억원 이상. 수천 개의 특허와 기술 스타트업의 중심지입니다.',
        'abu_global': '글로벌 허브', 'abu_global_desc': '90개국 이상의 다양한 국가에서 온 학생들. 모든 전공 수업은 영어로 진행됩니다.',
        'dash_checklist': '입학 체크리스트', 'dash_quick': '빠른 작업', 'dash_advisor': 'AI 어드바이저',
        'dash_tip': '오늘의 팁: ',
        'dash_passport_warn': '여권이 업로드되지 않았거나 확인되지 않았습니다.',
        'dash_sop_ready': 'SOP Lab을 통해 첫 번째 초안이 준비되었습니다!',
        'dash_stats_summary': '귀하의 전반적인 준비 수준: ',
        'tab_blog': '블로그', 'tab_courses': '강좌', 'btn_learn': '학습하기', 'btn_read': '읽기',
        'ai_tutor': 'AI 튜터', 'lesson_chat': '이 레슨에 대해 궁금한 점을 물어보세요...'
    }
}

def get_badges(tg_id):
    user = db.get_user(tg_id)
    if not user: return []
    badges = []
    if (user.get('ielts') or 0) >= 7.5: badges.append({"id":"lang","icon":"🌍","label":"Language Master"})
    if (user.get('gpa') or 0) >= 90: badges.append({"id":"gpa","icon":"🎓","label":"GPA Scholar"})
    
    docs_list = db.get_docs(tg_id)
    verified_docs = 0
    docs_dict = {}
    for d in docs_list:
        if d['checked']: verified_docs += 1
        dn = d['doc_name'].lower()
        if 'pasport' in dn or 'passport' in dn: docs_dict['Passport'] = d
    
    p_items = db.get_portfolio(tg_id)
    if len([i for i in p_items if i['verified']]) >= 3: 
        badges.append({"id":"port","icon":"📁","label":"Portfolio King"})
    
    if user.get('passport_face_path') and docs_dict.get('Passport', {}).get('checked'):
        badges.append({"id":"id","icon":"🆔","label":"Verified Identity"})
    
    return badges

def call_openai_text(prompt):
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}, timeout=20).json()
        return res['choices'][0]['message']['content']
    except: return "AI Error: Could not generate text."

@app.context_processor
def inject_t():
    lang = session.get('lang', 'uz')
    # Get nearest upcoming deadline for the countdown
    deadlines = db.get_admin_deadlines()
    upcoming = [d for d in deadlines if d['date'] > datetime.datetime.now().strftime('%Y-%m-%d')]
    upcoming.sort(key=lambda x: x['date'])
    next_dl = upcoming[0] if upcoming else {'date': '2026-09-01', 'name': 'KAIST Opening'}
    
    user = None
    docs_dict = {}
    if session.get('tg_id'):
        user_data = db.get_user(session['tg_id'])
        if user_data:
            user = dict(user_data)
            user['badges'] = get_badges(session['tg_id'])
            
            # Fetch student profile progress for IELTS
            c_db = db._conn()
            profile = c_db.execute("SELECT * FROM student_profiles WHERE tg_id=? LIMIT 1", (session['tg_id'],)).fetchone()
            if profile:
                user['ielts_profile'] = dict(profile)
                avg_score = c_db.execute("SELECT AVG(score) FROM daily_tasks WHERE tg_id=? AND completed=1 AND score>0", (session['tg_id'],)).fetchone()[0]
                if avg_score:
                    user['estimated_band'] = f"{round(avg_score, 1)}"
                else:
                    # More conservative defaults: Beginner: 3.5, Inter: 5.0, Advanced: 6.5
                    lv_map = {"beginner": "3.5", "intermediate": "5.0", "advanced": "6.5"}
                    user['estimated_band'] = lv_map.get(profile['level'], "4.0")
            c_db.close()
            
            docs_list = db.get_docs(session['tg_id'])
            for d in docs_list:
                dn = d['doc_name'].lower()
                if 'pasport' in dn or 'passport' in dn: docs_dict['Passport'] = d
                elif 'transkript' in dn or 'transcript' in dn or 'diplom' in dn: docs_dict['Transcript'] = d
                elif 'tavsiya' in dn or 'recommendation' in dn: docs_dict['Recommendation'] = d
                elif 'sop' in dn: docs_dict['SOP'] = d

    return {"lang": lang, "t": T.get(lang, T['uz']), "next_deadline": next_dl, "user": user, "docs": docs_dict}

@app.route('/api/leaderboard')
def api_leaderboard():
    users = db.get_all_users()
    # Return top 10 with limited info
    top_10 = []
    for i, u in enumerate(users[:10]):
        top_10.append({
            "rank": i+1,
            "name": u['name'],
            "username": u['username'],
            "xp": u['xp'],
            "level": u['level'],
            "avatar": u['avatar_path'] if u.get('avatar_path') else f"https://ui-avatars.com/api/?name={u['name'].replace(' ', '+')}"
        })
    return jsonify(top_10)

@app.route('/api/set_lang', methods=['POST'])
def api_lang():
    session['lang'] = request.json.get('lang', 'uz')
    return jsonify({'ok': True})

# ── PAGES (MPA ROUTER) ──
PAGES = ['skills', 'predictor', 'sop', 'research', 'email', 'interview', 'roadmap', 'network', 'scholarships', 'portfolio', 'labs', 'stats', 'documents', 'admin', 'settings', 'about', 'blog']

@app.route('/')
def index():
    return render_template('skills.html', active_page='skills')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('user')
        pw = request.form.get('pw')
        admin_pass = os.getenv('ADMIN_PASS')
        
        # Check against .env and DB
        is_authenticated = False
        if admin_pass and user == 'admin' and pw == admin_pass:
            is_authenticated = True
        elif session.get('tg_id'):
            u = db.get_user(session['tg_id'])
            if u and u.get('is_admin'):
                is_authenticated = True
                
        if is_authenticated:
            session['admin_logged_in'] = True
            return redirect('/admin')
            
    return render_template('admin_login.html', active_page='admin')

@app.route('/p/<username>')
def public_profile(username):
    user = db.get_user_by_username(username)
    if not user: return "User not found", 404
    if not user.get('is_public', 1): return "This profile is private", 403
    
    u = dict(user)
    u['badges'] = get_badges(u['tg_id'])
    
    # Get portfolio items
    c = db._conn()
    items = c.execute("SELECT * FROM portfolio WHERE tg_id=? AND verified=1", (u['tg_id'],)).fetchall()
    c.close()
    
    return render_template('public_profile.html', u=u, items=[dict(i) for i in items])

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json or {}
    upd = {}
    if 'name' in data: upd['name'] = data['name']
    if 'username' in data: 
        new_un = data['username'].strip().lower().replace(' ', '_')
        # Check uniqueness
        existing = db.get_user_by_username(new_un)
        if existing and existing['tg_id'] != tg_id:
            return jsonify({'ok': False, 'error': 'Username already taken'})
        upd['username'] = new_un
    if 'is_public' in data: upd['is_public'] = 1 if data['is_public'] else 0
    if 'lang' in data: 
        upd['lang'] = data['lang']
        session['lang'] = data['lang']
    if 'university' in data: upd['university'] = data['university']
    if 'field' in data: upd['field'] = data['field']
    if 'theme' in data: upd['theme'] = data['theme']
    if 'tips_enabled' in data: upd['tips_enabled'] = 1 if data['tips_enabled'] else 0
    if 'show_avatar' in data: upd['show_avatar'] = 1 if data['show_avatar'] else 0
        
    db.update_user(tg_id, **upd)
    return jsonify({'ok': True})

# ── AVATAR UPLOAD ──
@app.route('/api/upload/avatar', methods=['POST'])
def upload_avatar():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400

    f = request.files['file']
    if f.filename == '': return jsonify({'error': 'Empty filename'}), 400
    
    # Check file size (max 5MB)
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large (max 5MB)'}), 400

    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
    if ext not in ['jpg', 'jpeg', 'png', 'webp']: 
        return jsonify({'error': 'Invalid format (Use JPG, PNG, WEBP)'}), 400

    fname = f"avatar_{tg_id}.{ext}"
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    f.save(fpath)
    db.update_user(tg_id, avatar_path=f"/static/uploads/{fname}")
    return jsonify({'ok': True, 'avatar': f"/static/uploads/{fname}"})

# ── PASSPORT OCR + FACE EXTRACTION ──
@app.route('/api/passport/scan', methods=['POST'])
def passport_scan():
    import base64, json as pyjson
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400

    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
    fname = f"{uuid.uuid4()}_passport.{ext}"
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    f.save(fpath)

    # Build base64 for GPT-4o Vision
    with open(fpath, 'rb') as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode('utf-8')

    prompt = """Analyze this passport image. Extract the following fields and return ONLY valid JSON:
{
  "full_name": "First Last",
  "date_of_birth": "YYYY-MM-DD",
  "nationality": "Country Name",
  "passport_number": "AB1234567",
  "has_face_photo": true
}
If a field is not visible, use null. Return ONLY the JSON, no other text."""

    res_text = call_openai_json(prompt, img_b64)
    
    try:
        data = pyjson.loads(res_text)
    except Exception:
        return jsonify({'ok': False, 'error': 'Could not read passport'})

    # Save extracted passport data to DB
    upd = {}
    if data.get('full_name'): upd['name'] = data['full_name']
    if data.get('date_of_birth'): upd['passport_dob'] = data['date_of_birth']
    if data.get('nationality'): upd['passport_nationality'] = data['nationality']
    if data.get('passport_number'): upd['passport_number'] = data['passport_number']
    
    # Save passport face as well (stored as source ref for face comparison)
    upd['passport_face_path'] = f"/static/uploads/{fname}"
    
    if upd: db.update_user(tg_id, **upd)
    
    db.update_doc_status(tg_id, "Passport", 1, f"/static/uploads/{fname}")

    return jsonify({'ok': True, 'data': data})

# ── FACE SIMILARITY VERIFICATION ──
@app.route('/api/face/verify', methods=['POST'])
def face_verify():
    import base64, json as pyjson
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401

    u = db.get_user(tg_id)
    if not u or not u.get('passport_face_path'):
        return jsonify({'ok': False, 'error': 'Upload your passport first'})

    if 'file' not in request.files: return jsonify({'error': 'No selfie file'}), 400

    # Save selfie as new avatar too
    f = request.files['file']
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
    sname = f"selfie_{tg_id}.{ext}"
    spath = os.path.join(app.config['UPLOAD_FOLDER'], sname)
    f.save(spath)

    # Load both images as base64
    with open(spath, 'rb') as sf:
        selfie_b64 = base64.b64encode(sf.read()).decode('utf-8')

    # Load passport image
    passport_disk_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        u['passport_face_path'].lstrip('/')
    )
    try:
        with open(passport_disk_path, 'rb') as pf:
            passport_b64 = base64.b64encode(pf.read()).decode('utf-8')
    except Exception:
        return jsonify({'ok': False, 'error': 'Passport image not accessible'})

    prompt = """Compare the two faces in these two images. 
Image 1 is a selfie/profile photo. Image 2 is a passport.
Return ONLY valid JSON:
{
  "match": true or false,
  "confidence": 0-100,
  "reason": "one sentence explanation"
}"""

    import requests as req_lib
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{selfie_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{passport_b64}"}}
    ]}]
    try:
        res = req_lib.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.1,
                  "response_format": {"type": "json_object"}},
            timeout=30
        ).json()
        result = pyjson.loads(res['choices'][0]['message']['content'])
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

    # If match, save selfie as profile avatar
    if result.get('match'):
        db.update_user(tg_id, avatar_path=f"/static/uploads/{sname}")
        db.update_doc_status(tg_id, "Passport", 1)

    return jsonify({'ok': True, 'result': result, 'avatar': f"/static/uploads/{sname}"})

# ── AI FEATURES (PREDICTOR, SOP, INTERVIEW) ──
@app.route('/api/predictor/predict', methods=['POST'])
def api_prediction_run():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    u = db.get_user(tg_id)
    prompt = f"Act as an elite KAIST admission analyst. Analyze this profile: GPA {u['gpa']}/100, IELTS {u['ielts']}, Awards: {u['awards']}, Field: {u['field']}. Provide a 3-paragraph brutally honest admission prediction."
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}, timeout=20).json()
        text = res['choices'][0]['message']['content']
    except Exception as e:
        print(f"AI Predictor Error: {e}")
        text = "AI Analysis is currently unavailable. Please try again in 1 minute."
    return jsonify({'prediction': text})

@app.route('/api/sop/generate', methods=['POST'])
def api_sop_generate_run():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    u = db.get_user(tg_id)
    prompt = f"Write a 4-paragraph Statement of Purpose draft for KAIST. Field: {u['field']}. Must be creative, challenge-oriented, and caring. Do not include placeholders, make it sound like a real applicant."
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
             json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}, timeout=20).json()
        text = res['choices'][0]['message']['content']
    except Exception as e:
        print(f"SOP Generator Error: {e}")
        text = "SOP generation failed. Please check your connection and try again."
    return jsonify({'sop': text})

@app.route('/api/interview/question')
def api_int_question_run():
    questions = [
        "Why did you choose KAIST over other top universities?",
        "Describe a difficult engineering problem you solved.",
        "How do you plan to contribute to Korean society after graduating?",
        "What specific KAIST lab aligns with your research goals?"
    ]
    import random
    return jsonify({'question': random.choice(questions)})

@app.route('/api/interview/analyze', methods=['POST'])
def api_int_analyze_run():
    data = request.json
    q = data.get('question', '')
    ans = data.get('answer', '')
    prompt = f"Act as a KAIST Interviewer. The question was: '{q}'. The applicant answered: '{ans}'. Give 3 sentences of constructive feedback. Be strict."
    import requests
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
             json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}, timeout=20).json()
        text = res['choices'][0]['message']['content']
    except: text = "Could not analyze answer."
    return jsonify({'analysis': text})

# ── PHASE 2: LAB MATCHER & COLD EMAILER ──
@app.route('/api/labs/match', methods=['POST'])
def api_labs_match():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    u = db.get_user(tg_id)
    field = u.get('field', '')
    
    # Try DB first
    db_matches = db.get_lab_matches(field)
    
    # If few matches, use AI to suggest
    prompt = f"The student is interested in {field}. Suggest 3 real or highly plausible KAIST labs (Name, Research Focus, PI). Return ONLY valid JSON array: [{{'name': '...', 'focus': '...', 'pi': '...'}}, ...]"
    import requests
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
             json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}, timeout=20).json()
        ai_labs = json.loads(res['choices'][0]['message']['content']).get('labs', [])
    except: ai_labs = []
    
    return jsonify({"db_labs": db_matches, "ai_labs": ai_labs})

@app.route('/api/email/generate', methods=['POST'])
def api_email_gen():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    u = db.get_user(tg_id)
    target_lab = request.json.get('lab', 'a KAIST Laboratory')
    
    prompt = f"Write a professional cold email from a prospective PhD student to {target_lab}. Student Profile: GPA {u['gpa']}, Field: {u['field']}, Research: {u['research']} papers. The tone should be respectful, precise, and show deep interest in their specific work at KAIST. Return the response in this format:\nSubject: [Subject Line]\n\n[Email Body]"
    import requests
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
             json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}, timeout=20).json()
        full_text = res['choices'][0]['message']['content']
        if "Subject:" in full_text:
            parts = full_text.split("\n\n", 1)
            subj = parts[0].replace("Subject:", "").strip()
            body = parts[1] if len(parts) > 1 else full_text
        else:
            subj = f"Inquiry regarding research at {target_lab}"
            body = full_text
    except: 
        subj = "Error"
        body = "Error generating email."
    
    return jsonify({"subject": subj, "body": body})

# ── PHASE 3: SOP REVIEWER & VOICE INTERVIEW ──
@app.route('/api/sop/review', methods=['POST'])
def api_sop_review():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    sop_text = request.json.get('sop', '')
    if not sop_text: return jsonify({'error': 'No text provided'}), 400
    
    prompt = f"Review the following SOP for KAIST admission based on their core values: Creativity, Challenge, and Caring. Provide a score from 1 to 10 and specific feedback for improvement. Return ONLY valid JSON: {{'score': 8, 'feedback': '...', 'creativity': 7, 'challenge': 9, 'caring': 8}}"
    import requests
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
             headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
             json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}, timeout=20).json()
        review = json.loads(res['choices'][0]['message']['content'])
    except: review = {"error": "AI Review failed"}
    
    return jsonify(review)

# ── PHASE 4: TELEGRAM AUTOMATION ──
def send_roadmap_reminders():
    """Background task to send reminders for tomorrow's deadlines."""
    import time
    from datetime import datetime, timedelta
    while True:
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            c = db._conn()
            items = c.execute("SELECT r.*, u.name FROM user_roadmap r JOIN users u ON r.tg_id = u.tg_id WHERE r.date = ? AND r.done = 0", (tomorrow,)).fetchall()
            c.close()

            for item in items:
                msg = f"🔔 *Deadline Reminder*\n\nHurmatli {item['name']},\nErtaga sizda quyidagi vazifa muddati tugaydi:\n\n📌 *{item['title']}*\n\nMuaffaqiyat tilaymiz! 🚀"
                # Call TG bot (simulated via requests)
                # requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": item['tg_id'], "text": msg, "parse_mode": "Markdown"})
                print(f"DEBUG: Sent reminder to {item['tg_id']} for {item['title']}")
            
            # Run once a day (check every 24 hours)
            time.sleep(86400)
        except Exception as e:
            print(f"Reminder Thread Error: {e}")
            time.sleep(3600)

# Prevention of multiple threads in dev/prod
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    reminder_thread = threading.Thread(target=send_roadmap_reminders, daemon=True)
    reminder_thread.start()


@app.route('/courses')
def courses_view():
    cat = request.args.get('category')
    c = db._conn()
    if cat:
        courses = c.execute("SELECT * FROM courses WHERE category=?", (cat,)).fetchall()
    else:
        courses = c.execute("SELECT * FROM courses").fetchall()
    c.close()
    return render_template('courses.html', active_page='courses', courses=courses, current_cat=cat)

@app.route('/<page>')
def render_page(page):
    if page == 'admin':
        # Admin requires either .env login session OR telegram db admin status
        tg_admin = False
        if session.get('tg_id'):
            u = db.get_user(session['tg_id'])
            if u and u.get('is_admin'): tg_admin = True
            
        if not session.get('admin_logged_in') and not tg_admin:
            return redirect('/admin/login')
                
    if page in PAGES:
        return render_template(f'{page}.html', active_page=page)
    return redirect('/')

# ── AUTH & DATA API ──
@app.route('/api/auth/otp', methods=['POST'])
def api_auth_otp():
    otp = request.json.get('otp')
    user = db.get_user_by_otp(otp)
    if user:
        session['tg_id'] = user['tg_id']
        session['name'] = user['name']
        # Clear OTP after use
        db.update_user(user['tg_id'], otp=None)
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Invalid or expired code'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/me')
def api_me():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'ok': False, 'logged_in': False})
    u = db.get_user(tg_id)
    if not u: return jsonify({'ok': False, 'logged_in': False})
    docs = db.get_docs(tg_id)
    
    docs_dict = {}
    if docs:
        for d in docs:
            dn = d['doc_name'].lower()
            if 'pasport' in dn or 'passport' in dn: docs_dict['Passport'] = dict(d)
            elif 'transkript' in dn or 'transcript' in dn or 'diplom' in dn: docs_dict['Transcript'] = dict(d)
            elif 'tavsiya' in dn or 'recommendation' in dn: docs_dict['Recommendation'] = dict(d)
            elif 'sop' in dn: docs_dict['SOP'] = dict(d)
            
    return jsonify({
        'ok': True,
        'logged_in': True,
        'user': {
            'name': u['name'],
            'username': u['username'] or '',
            'xp': u['xp'],
            'level': u['level'],
            'gpa': u['gpa'],
            'ielts': u['ielts'],
            'research': u['research'],
            'awards': u['awards'],
            'lang': u['lang'] if 'lang' in u.keys() else 'uz',
            'is_public': u['is_public'] if 'is_public' in u.keys() else 1,
            'tips_enabled': u['tips_enabled'] if 'tips_enabled' in u.keys() else 1,
            'university': u['university'] if 'university' in u.keys() else '',
            'field': u['field'] if 'field' in u.keys() else '',
            'theme': u['theme'] if 'theme' in u.keys() else 'glass',
            'avatar_path': u['avatar_path'] if 'avatar_path' in u.keys() else None,
            'show_avatar': u['show_avatar'] if 'show_avatar' in u.keys() else 1,
            'passport_dob': u['passport_dob'] if 'passport_dob' in u.keys() else None,
            'passport_nationality': u['passport_nationality'] if 'passport_nationality' in u.keys() else None,
            'passport_number': u['passport_number'] if 'passport_number' in u.keys() else None,
            'badges': get_badges(tg_id),
            'estimated_band': (lambda: (
                c_temp := db._conn(),
                p := c_temp.execute("SELECT level FROM student_profiles WHERE tg_id=? LIMIT 1", (tg_id,)).fetchone(),
                avg := c_temp.execute("SELECT AVG(score) FROM daily_tasks WHERE tg_id=? AND completed=1 AND score>0", (tg_id,)).fetchone()[0],
                c_temp.close(),
                f"{round(avg, 1)}" if avg else ({"beginner": "3.5", "intermediate": "5.0", "advanced": "6.5"}.get(p[0] if p else "", "N/A"))
            )[-1])()
        },
        'docs': [dict(d) for d in docs] if docs else [],
        'docs_dict': docs_dict
    })

# Clean Array Endpoints (Prevents the empty UI bug)
@app.route('/api/labs')
def api_labs(): return jsonify(db.get_admin_labs())

@app.route('/api/scholarships')
def api_schol(): return jsonify(db.get_admin_scholarships())

@app.route('/api/roadmap')
def api_road(): return jsonify(db.get_admin_roadmap())

@app.route('/api/vocab')
def api_vocab(): return jsonify(db.get_admin_vocab())

@app.route('/api/deadlines')
def api_dl(): return jsonify(db.get_admin_deadlines())

@app.route('/api/admin/stats')
def api_admin_stats():
    u_list = db.get_all_users()
    p_list = db.get_all_portfolio_items()
    return jsonify({
        'ok': True,
        'user_count': len(u_list),
        'item_count': len(p_list),
        'users': u_list[:100],
        'items': p_list[:20],        # Used by admin.html
        'recent_items': p_list[:20], # Legacy alias
        'deadlines': db.get_admin_deadlines(),
        'scholarships': db.get_admin_scholarships()
    })

@app.route('/api/admin/add', methods=['POST'])
def api_admin_add():
    table = request.json.get('table')
    data = request.json.get('data')
    if not table or not data: return jsonify({'error': 'Missing data'})
    db.add_admin_item(table, **data)
    return jsonify({'ok': True})

@app.route('/api/admin/delete', methods=['POST'])
def api_admin_delete():
    table = request.json.get('table')
    item_id = request.json.get('id')
    if not table or not item_id: return jsonify({'error': 'Missing data'})
    db.delete_admin_item(table, item_id)
    return jsonify({'ok': True})

@app.route('/api/portfolio/approve/<int:item_id>', methods=['POST'])
def api_port_approve(item_id):
    if not session.get('admin_logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    c = db._conn()
    item = c.execute("SELECT * FROM portfolio WHERE id=?", (item_id,)).fetchone()
    if not item: 
        c.close()
        return jsonify({'error': 'Not found'}), 404
    c.execute("UPDATE portfolio SET verified=1 WHERE id=?", (item_id,))
    c.commit()
    c.close()
    return jsonify({'ok': True})

@app.route('/api/portfolio')
def api_port():
    tg_id = session.get('tg_id')
    return jsonify(db.get_portfolio(tg_id) if tg_id else [])

# ── NETWORK & RESEARCH ──
@app.route('/api/network/users')
def api_net_users():
    tg_id = session.get('tg_id')
    users = db.get_all_users()
    # Filter out current user and private profiles
    res = [u for u in users if u['tg_id'] != tg_id and u.get('is_public', 1)]
    return jsonify({'ok': True, 'users': res})

@app.route('/api/network/connect', methods=['POST'])
def api_net_connect():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    to_id = request.json.get('to_id')
    if not to_id: return jsonify({'error': 'Missing ID'}), 400
    
    # Check if already connected (simple implementation)
    c = db._conn()
    existing = c.execute("SELECT * FROM connections WHERE from_id=? AND to_id=?", (tg_id, to_id)).fetchone()
    if not existing:
        c.execute("INSERT INTO connections (from_id, to_id, status, created_at) VALUES (?, ?, 'connected', ?)", 
                  (tg_id, to_id, datetime.datetime.now().isoformat()))
        c.commit()
    c.close()
    return jsonify({'ok': True})

@app.route('/api/research/labs')
def api_res_labs():
    major = request.args.get('major', '')
    labs = db.get_all_labs()
    if major:
        labs = [l for l in labs if major.lower() in l['major'].lower()]
    return jsonify({'ok': True, 'labs': labs})


@app.route('/api/roadmap/personal', methods=['GET', 'POST', 'DELETE'])
def api_road_personal():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        return jsonify(db.get_user_roadmap(tg_id))
    elif request.method == 'POST':
        title = request.json.get('title')
        date = request.json.get('date', '')
        if not title: return jsonify({'error': 'Missing title'}), 400
        db.add_roadmap_item(tg_id, title, date)
        return jsonify({'ok': True})
    elif request.method == 'DELETE':
        item_id = request.json.get('id')
        if not item_id: return jsonify({'error': 'Missing id'}), 400
        db.delete_roadmap_item(tg_id, item_id)
        return jsonify({'ok': True})

@app.route('/api/community/chat', methods=['GET', 'POST'])
def api_community_chat():
    if request.method == 'GET':
        return jsonify(db.get_messages())
    elif request.method == 'POST':
        tg_id = session.get('tg_id')
        if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
        text = request.json.get('text')
        name = session.get('name', 'Anonymous')
        if not text: return jsonify({'error': 'Missing text'}), 400
        db.add_message(tg_id, name, text)
        return jsonify({'ok': True})


@app.route('/courses')
def course_list():
    cat = request.args.get('category')
    courses = db.get_courses(cat)
    return render_template('courses.html', active_page='courses', courses=courses, current_cat=cat)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    lessons = db.get_lessons(course_id)
    tg_id = session.get('tg_id')
    progress = db.get_user_progress(tg_id) if tg_id else []
    
    # Simple logic to find the course title for the breadcrumb/header
    c = db._conn()
    course = c.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    c.close()
    
    if not course: return redirect('/courses')
    return render_template('course_viewer.html', active_page='courses', course=course, lessons=lessons, progress=progress)

@app.route('/lesson/<int:lesson_id>')
def lesson_view(lesson_id):
    lesson = db.get_lesson(lesson_id)
    if not lesson: return redirect('/courses')
    
    # Get course info too
    c = db._conn()
    course = c.execute("SELECT * FROM courses WHERE id=?", (lesson['course_id'],)).fetchone()
    c.close()
    
    return render_template('lesson.html', active_page='courses', lesson=lesson, course=course)

@app.route('/api/lesson/complete', methods=['POST'])
def api_lesson_complete():
    tg_id = session.get('tg_id')
    lesson_id = request.json.get('lesson_id')
    if not tg_id or not lesson_id: return jsonify({'error': 'Unauthorized'}), 401
    db.complete_lesson(tg_id, lesson_id)
    return jsonify({'ok': True})

@app.route('/api/lesson/chat', methods=['POST'])
def api_lesson_chat():
    lesson_id = request.json.get('lesson_id')
    user_msg = request.json.get('message')
    if not lesson_id or not user_msg: return jsonify({'error': 'Missing data'}), 400
    
    lesson = db.get_lesson(lesson_id)
    if not lesson: return jsonify({'error': 'Lesson not found'}), 404
    
    system_prompt = lesson['ai_prompt'] or "You are a helpful language tutor."
    prompt = f"System Context: {system_prompt}\nStudent: {user_msg}\nTutor:"
    
    response = call_openai_text(prompt)
    return jsonify({'ok': True, 'response': response})


# ── ADAPTIVE IELTS LEARNING ROUTES ──

@app.route('/course/<int:course_id>/assess')
def course_assess(course_id):
    if not session.get('tg_id'): return redirect('/')
    c = db._conn()
    course = c.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    c.close()
    if not course: return redirect('/courses')
    # Check if profile already exists
    profile = db.get_student_profile(session['tg_id'], course_id)
    if profile:
        return redirect(f'/course/{course_id}/learn')
    return render_template('assess.html', active_page='courses', course=course)

@app.route('/course/<int:course_id>/learn')
def course_learn(course_id):
    tg_id = session.get('tg_id')
    if not tg_id: return redirect('/')
    c = db._conn()
    course = c.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    c.close()
    if not course: return redirect('/courses')
    profile = db.get_student_profile(tg_id, course_id)
    if not profile: return redirect(f'/course/{course_id}/assess')
    tasks = db.get_today_tasks(tg_id, course_id)
    vocab_today = db.get_vocab_count_today(tg_id)
    import json
    strategy = json.loads(profile['strategy_json']) if profile.get('strategy_json') else {}
    return render_template('learn.html', active_page='courses', course=course,
                           profile=profile, tasks=tasks, strategy=strategy, vocab_today=vocab_today)

@app.route('/vocab')
def vocab_page():
    tg_id = session.get('tg_id')
    if not tg_id: return redirect('/')
    words = db.get_vocab(tg_id, limit=200)
    today_count = db.get_vocab_count_today(tg_id)
    return render_template('vocab.html', active_page='courses', words=words, today_count=today_count)

@app.route('/listening/<int:session_id>')
def listening_page(session_id):
    tg_id = session.get('tg_id')
    if not tg_id: return redirect('/')
    s = db.get_listening_session(session_id)
    if not s: return redirect('/courses')
    import json
    questions = json.loads(s['questions_json']) if s.get('questions_json') else []
    blanks = json.loads(s['blanks_json']) if s.get('blanks_json') else []
    return render_template('listening.html', active_page='courses',
                           session=s, session_id=session_id, questions=questions, blanks=blanks)

# ── ASSESSMENT API ──
@app.route('/api/assess/question', methods=['POST'])
def api_assess_question():
    data = request.json
    history = data.get('history', [])
    course_type = data.get('course_type', 'English')
    q_num = len([h for h in history if h['role'] == 'assistant']) + 1

    if q_num > 6:
        return jsonify({'done': True})

    sys_prompt = f"""You are an expert {course_type} language assessment tutor. 
    Ask question #{q_num} of 6 to assess the student's current {course_type} language level (A1-C1/Beginner to Advanced).
    Questions should progressively get harder. Mix: vocabulary knowledge, grammar understanding, reading comprehension.
    After 6 questions you will analyze. Ask ONE question at a time. Be encouraging but professional.
    Return JSON: {{"question": "...", "hint": "..."}}"""

    messages = [{"role": "system", "content": sys_prompt}]
    for h in history:
        messages.append({"role": h['role'], "content": h['content']})

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": messages, "response_format": {"type": "json_object"}}, timeout=20).json()
        result = json.loads(res['choices'][0]['message']['content'])
        return jsonify({'ok': True, 'question': result.get('question', ''), 'hint': result.get('hint', ''), 'num': q_num})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/api/assess/complete', methods=['POST'])
def api_assess_complete():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    course_id = data.get('course_id')
    history = data.get('history', [])
    exam_date = data.get('exam_date', '')
    target_score = float(data.get('target_score', 7.0))
    course_type = data.get('course_type', 'English')

    prompt = f"""Based on this assessment conversation, determine the student's {course_type} level and create a personalized learning strategy.
    
Assessment Q&A: {json.dumps(history)}
Target Score: {target_score} | Exam Date: {exam_date} | Language: {course_type}

Return JSON:
{{
  "level": "beginner|intermediate|advanced",
  "cefr": "A1|A2|B1|B2|C1",
  "summary": "2-sentence assessment summary",
  "strategy": {{
    "daily_vocab_goal": 30,
    "focus_areas": ["vocabulary", "grammar", "listening", "reading"],
    "weekly_plan": {{
      "Monday": "Vocabulary + Reading",
      "Tuesday": "Grammar + Listening",
      "Wednesday": "Writing + Vocab review",
      "Thursday": "Full practice test",
      "Friday": "Weak area focus",
      "Saturday": "Listening marathon",
      "Sunday": "Review + Rest"
    }},
    "roadmap": [
      {{"week": 1, "goal": "Building basic vocabulary and grammar awareness", "milestone": "Master 200 common IELTS words"}},
      {{"week": 2, "goal": "Introduction to Listening and Reading techniques", "milestone": "Complete 5 mock Listening sections"}},
      {{"week": 3, "goal": "Focusing on Writing Task 1 and Speaking flow", "milestone": "Write 3 Task 1 reports with band 6.0+ feedback"}},
      {{"week": 4, "goal": "Advanced Grammar and Reading speed", "milestone": "Finish 3 IELTS Reading passages in under 60 mins"}}
    ],
    "tip": "One key tip for this student"
  }}
}}"""

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}}, timeout=25).json()
        result = json.loads(res['choices'][0]['message']['content'])
        level = result.get('level', 'beginner')
        strategy = json.dumps(result.get('strategy', {}))
        db.save_student_profile(tg_id, course_id, level, target_score, exam_date, strategy)
        return jsonify({'ok': True, 'level': level, 'cefr': result.get('cefr'), 'summary': result.get('summary'), 'course_id': course_id})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

# ── DAILY TASKS API ──
@app.route('/api/daily/generate', methods=['POST'])
def api_daily_generate():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    course_id = request.json.get('course_id')
    profile = db.get_student_profile(tg_id, course_id)
    if not profile: return jsonify({'error': 'No profile'}), 400

    strategy = json.loads(profile['strategy_json']) if profile.get('strategy_json') else {}
    today_weekday = datetime.datetime.now().strftime('%A')
    today_plan = strategy.get('weekly_plan', {}).get(today_weekday, 'General practice')

    prompt = f"""Generate today's ({today_weekday}) adaptive learning tasks for a {profile['level']} English/IELTS student.
Today's focus: {today_plan}
Target score: {profile['target_score']} IELTS band.

Return JSON array of exactly 4 tasks:
[
  {{"type": "vocab", "title": "Today's Vocabulary", "instruction": "Read this text and identify 30 new words:", "text": "...100 word sample IELTS-level text...", "words_needed": 30}},
  {{"type": "grammar", "title": "Grammar Focus", "topic": "...", "exercise": "...grammar exercise...", "answer_key": "..."}},
  {{"type": "reading", "title": "Reading Comprehension", "passage": "...200 word passage...", "questions": ["Q1?", "Q2?", "Q3?"], "answers": ["A1", "A2", "A3"]}},
  {{"type": "listening", "title": "Listening Exercise", "generate": true}}
]"""

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}}, timeout=30).json()
        raw = json.loads(res['choices'][0]['message']['content'])
        tasks_list = raw if isinstance(raw, list) else raw.get('tasks', [])
        db.save_daily_tasks(tg_id, course_id, [{'type': t['type'], 'content': t} for t in tasks_list])
        return jsonify({'ok': True, 'tasks': tasks_list})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/api/task/submit', methods=['POST'])
def api_task_submit():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    task_id = data.get('task_id')
    answer = data.get('answer', '')
    expected = data.get('expected', '')
    task_type = data.get('task_type', 'general')

    prompt = f"""You are an IELTS examiner. Evaluate this student's {task_type} answer.
Expected answer/key: {expected}
Student's answer: {answer}

Return JSON: {{"score": 8.5, "feedback": "Specific actionable feedback", "correct": true, "correction": "corrected version if wrong"}}"""

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}}, timeout=20).json()
        result = json.loads(res['choices'][0]['message']['content'])
        if task_id:
            db.complete_task(task_id, result.get('feedback', ''), result.get('score', 0))
        return jsonify({'ok': True, **result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/api/course/lesson', methods=['POST'])
def api_course_lesson():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    course_id = request.json.get('course_id')
    topic = request.json.get('topic') # Optional specific topic
    
    profile = db.get_student_profile(tg_id, course_id)
    if not profile: return jsonify({'error': 'No profile'}), 400
    
    prompt = f"""You are a professional IELTS Tutor. Generate a THEORETICAL lesson for a {profile['level']} student.
Target: IELTS {profile['target_score']}.
Topic: {topic if topic else 'Choose a critical IELTS technique (e.g. Scanning, Cohesion, Task 2 structure)'}

Return JSON:
{{
  "title": "Lesson Title",
  "topic": "Specific Topic",
  "content": "Detailed explanation with examples (Markdown formatted, approx 300 words)",
  "quiz_question": "One simple check question",
  "quiz_answer": "Expected answer"
}}"""

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}}, timeout=30).json()
        lesson = json.loads(res['choices'][0]['message']['content'])
        # Save as a task so it persists in the dashboard
        db.save_daily_tasks(tg_id, course_id, [{
            'type': 'lesson',
            'content': lesson
        }])
        return jsonify({'ok': True, 'lesson': lesson})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

# ── VOCAB API ──
@app.route('/api/vocab/add', methods=['POST'])
def api_vocab_add():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    words_raw = request.json.get('words', '')
    context = request.json.get('context', '')

    # Parse words (comma or newline separated)
    word_list = [w.strip() for w in words_raw.replace(',', '\n').split('\n') if w.strip()]

    results = []
    for word in word_list[:50]:  # Cap at 50 per call
        # AI translate
        translation_prompt = f"Translate '{word}' to Uzbek and Russian. Return JSON: {{\"word\": \"{word}\", \"uz\": \"...\", \"ru\": \"...\", \"example\": \"Use in sentence\"}}"
        try:
            res = requests.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": translation_prompt}],
                      "response_format": {"type": "json_object"}}, timeout=10).json()
            trans_data = json.loads(res['choices'][0]['message']['content'])
            translation = f"{trans_data.get('uz', '')} / {trans_data.get('ru', '')}"
            example = trans_data.get('example', '')
        except:
            translation = '(tarjima mavjud emas)'
            example = ''

        status = db.add_vocab(tg_id, word, translation, context or example)
        results.append({'word': word, 'translation': translation, 'status': status, 'example': example})

    today_count = db.get_vocab_count_today(tg_id)
    return jsonify({'ok': True, 'results': results, 'today_count': today_count})

@app.route('/api/vocab/quiz', methods=['POST'])
def api_vocab_quiz():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    words = db.get_vocab(tg_id, limit=50)
    if len(words) < 4: return jsonify({'error': 'Not enough words'}), 400
    import random
    sample = random.sample(words, min(10, len(words)))
    return jsonify({'ok': True, 'quiz': [{'id': w['id'], 'word': w['word'], 'translation': w['translation']} for w in sample]})

# ── LISTENING API ──
@app.route('/api/listening/generate', methods=['POST'])
def api_listening_generate():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    level = request.json.get('level', 'intermediate')
    topic = request.json.get('topic', 'academic life')

    # AI generates transcript with blanks
    prompt = f"""Create an IELTS {level} listening exercise about {topic}.
Return JSON:
{{
  "transcript": "Full 200-word passage (about 90 seconds when read aloud).",
  "display_text": "Same passage but with 10 key words replaced by [BLANK_1], [BLANK_2]... etc shown to student",
  "blanks": [{{"id": 1, "answer": "word1"}}, {{"id": 2, "answer": "word2"}}, ...],
  "questions": [
    {{"id": 1, "question": "What is the main topic?", "options": ["A", "B", "C", "D"], "answer": "A"}},
    {{"id": 2, "question": "According to the passage...", "options": ["A", "B", "C", "D"], "answer": "C"}}
  ]
}}"""

    try:
        res = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}],
                  "response_format": {"type": "json_object"}}, timeout=30).json()
        data = json.loads(res['choices'][0]['message']['content'])
        transcript = data.get('transcript', '')
        display_text = data.get('display_text', transcript)
        blanks = data.get('blanks', [])
        questions = data.get('questions', [])
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

    # Generate audio using gTTS (free)
    audio_path = None
    try:
        from gtts import gTTS
        import os
        audio_dir = os.path.join('static', 'audio')
        os.makedirs(audio_dir, exist_ok=True)
        fname = f"listen_{tg_id}_{int(datetime.datetime.now().timestamp())}.mp3"
        fpath = os.path.join(audio_dir, fname)
        tts = gTTS(text=transcript, lang='en', slow=False)
        tts.save(fpath)
        audio_path = f"/static/audio/{fname}"
    except Exception as e:
        print(f"gTTS error: {e}")
        audio_path = None

    session_id = db.save_listening_session(tg_id, transcript, audio_path or '', questions, blanks)
    return jsonify({'ok': True, 'session_id': session_id, 'display_text': display_text,
                    'blanks_count': len(blanks), 'audio_url': audio_path})

@app.route('/api/listening/submit', methods=['POST'])
def api_listening_submit():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    session_id = request.json.get('session_id')
    blank_answers = request.json.get('blank_answers', {})
    question_answers = request.json.get('question_answers', {})

    s = db.get_listening_session(session_id)
    if not s: return jsonify({'error': 'Session not found'}), 404

    blanks = json.loads(s['blanks_json']) if s.get('blanks_json') else []
    questions = json.loads(s['questions_json']) if s.get('questions_json') else []

    # Score blanks
    blank_score = 0
    blank_results = []
    for b in blanks:
        bid = str(b['id'])
        student_ans = blank_answers.get(bid, '').strip().lower()
        correct_ans = b['answer'].strip().lower()
        correct = student_ans == correct_ans
        if correct: blank_score += 1
        blank_results.append({'id': b['id'], 'correct': correct, 'answer': b['answer'], 'student': blank_answers.get(bid, '')})

    # Score MCQ
    mcq_score = 0
    mcq_results = []
    for q in questions:
        qid = str(q['id'])
        student_ans = question_answers.get(qid, '')
        correct = student_ans == q.get('answer', '')
        if correct: mcq_score += 1
        mcq_results.append({'id': q['id'], 'correct': correct, 'answer': q.get('answer'), 'student': student_ans})

    total = len(blanks) + len(questions)
    correct_total = blank_score + mcq_score
    score = round((correct_total / total * 9) if total > 0 else 0, 1)
    db.complete_listening_session(session_id, score)

    return jsonify({'ok': True, 'score': score, 'blank_results': blank_results, 'mcq_results': mcq_results,
                    'transcript': s['transcript']})

# ── SMART VAULT (VALIDATION AI) ──
def call_openai_json(prompt, img_b64=None):
    import json
    # GPT-4o-mini for maximum economy + intelligence
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    if img_b64:
        messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        
    data = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"}}
    try:
        res = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}, json=data, timeout=30).json()
        return res['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return '{"score": 0, "summary": "AI connection error"}'

def analyze_document(filepath, doc_type):
    import base64, json
    ext = filepath.rsplit('.', 1)[-1].lower()
    res_text = ""

    # ── BRANCH A: VISION (Images) ──
    if ext in ['png', 'jpg', 'jpeg', 'webp']:
        try:
            with open(filepath, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
        except: return '{"score": 0, "type": "File Read Error"}'
        
        prompt = f"Analyze this {doc_type} certificate. Extract: Official Score, Issuer, Date (YYYY-MM). Return strict JSON: {{\"score\": 8.5, \"summary\": \"Analysis result\", \"details\": {{\"date\":\"2024-01\", \"issuer\":\"Example Board\", \"level\":\"C1\"}} }}. No other text."
        
        # Use OpenAI gpt-4o-mini for superior Vision accuracy at low cost
        res_text = call_openai_json(prompt, img_b64)
        
    # ── BRANCH B: PDF ANALYSIS (Text Extraction) ──
    elif ext == 'pdf':
        try:
            import pypdf
        except ImportError:
            import PyPDF2 as pypdf
        try:
            reader = pypdf.PdfReader(filepath)
            text = ""
            for page in reader.pages[:3]:
                text += page.extract_text() + "\n"
            
            prompt = f"Analyze this {doc_type} text. Extract Official Score, Issuer, Date. Return strict JSON: {{\"score\": 8.5, \"summary\": \"PDF analysis result\", \"details\": {{\"date\":\"2024-01\", \"issuer\":\"Example\", \"level\":\"Verified\"}} }}.\nTEXT:\n{text[:5000]}"
            res_text = call_openai_json(prompt) # OpenAI for better reasoning on text
        except: res_text = '{"score":0, "summary":"PDF Error"}'

    # ── BRANCH B: CODE/TEXT ANALYSIS ──
    elif ext in ['py', 'js', 'cpp', 'java', 'html', 'css', 'txt']:
        try:
            with open(filepath, "r", encoding='utf-8', errors='ignore') as f:
                content = f.read()[:5000] # Limit to first 5k chars
        except: return '{"score": 0}'
        
        prompt = f"Evaluate this {doc_type} code file for KAIST admission level. Rate 1-100. Return strict JSON: {{\"score\": 85, \"summary\": \"Clean code, good logic\"}}.\nCODE:\n{content}"
        return call_openai_json(prompt)

    # ── BRANCH C: ARCHIVES (Zip) ──
    elif ext == 'zip':
        import zipfile
        try:
            with zipfile.ZipFile(filepath, 'r') as z:
                names = z.namelist()[:20] # List first 20 files
            summary = f"Project Archive. Contains: {', '.join(names)}"
            return f'{{"score": 70, "summary": "{summary}"}}'
        except: return '{"score": 0, "summary": "Invalid Zip"}'

    # ── BRANCH D: BINARY (Video/Other) ──
    else:
        res_text = '{"score": 0, "summary": "Media/Binary file stored."}'
        
    return res_text

@app.route('/api/documents/check', methods=['POST'])
def api_docs_check():
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'ok': False, 'error': 'Tizimga kirmagansiz (Unauthorized)'}), 401
    if 'file' not in request.files: return jsonify({'error': 'No file'})
    file = request.files['file']
    doc_type = request.form.get('type', 'Unknown')
    
    filename = f"{uuid.uuid4()}_{file.filename}"
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(fpath)
    
    # AI Compliance Check
    res_text = analyze_document(fpath, doc_type)
    try:
        # Strip markdown codeblocks if openAI wrapped it
        clean_text = res_text.strip()
        if clean_text.startswith('```'):
            lines = clean_text.split('\n')
            clean_text = '\n'.join(lines[1:-1])
        data = json.loads(clean_text)
        is_compliant = data.get('score', 0) > 0 or "Verified" in data.get('summary', '')
        reason = data.get('summary', 'Verified')
    except:
        is_compliant = True
        reason = 'Document stored (Manual verification required)'

    if is_compliant:
        DOC_MAPPING = {
            "Passport": "Pasport nusxasi",
            "Transcript": "Transkript (Apostil)",
            "Recommendation": "Tavsiya xati 1",
            "SOP": "SOP (yakuniy)"
        }
        db_doc_name = DOC_MAPPING.get(doc_type, "Passport" if "Passport" in doc_type else doc_type)
        db.update_doc_status(tg_id, db_doc_name, 1, f"/static/uploads/{filename}")
        
    return jsonify({'ok': True, 'compliant': is_compliant, 'reason': reason})

@app.route('/api/admin/export-db')
def api_admin_export_db():
    # Security: Use a password from environment variables or a default secret
    password = request.args.get('pw')
    secret = os.environ.get('EXPORT_PASSWORD', 'khub_secret_2026')
    if not password or password != secret:
        return "Unauthorized: Please provide the correct ?pw= parameter", 401
    
    # Send the database file defined in database.py
    try:
        return send_file(db.DB_FILE, as_attachment=True, download_name='khub.db')
    except Exception as e:
        return f"Export failed: {str(e)}", 500

@app.route('/api/vault/upload', methods=['POST'])
def api_vault_upload():
    import datetime, json
    tg_id = session.get('tg_id')
    if not tg_id: return jsonify({'error': 'Unauthorized'}), 401
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    doc_type = request.form.get('type', 'General Project')
    user_title = request.form.get('title', '').strip()
    user_desc = request.form.get('description', '').strip()
    
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'bin'
    filename = f"{uuid.uuid4().hex}.{ext}"
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(fpath)
    
    # ── AI ANALYSIS (ONLY FOR CERTIFICATES) ──
    certs = ["IELTS Certificate", "GPA Transcript", "Award / Achievement"]
    if doc_type in certs:
        res_text = analyze_document(fpath, doc_type)
        try: 
            ai_data = json.loads(res_text)
            full_meta = {
                "summary": user_desc if user_desc else ai_data.get('summary', ''),
                "score": ai_data.get('score', 0),
                "details": ai_data.get('details', {}),
                "ai_raw": ai_data.get('summary', '') if user_desc else ''
            }
            summary_txt = json.dumps(full_meta)
            score = float(ai_data.get('score', 0))
        except: 
            score = 0
            summary_txt = user_desc if user_desc else "Manual Upload"
    else:
        # Static storage for non-cert items (Code, Video, etc.)
        score = 0
        summary_txt = user_desc if user_desc else f"Stored {doc_type}"

    # Update Stats based on Score if it's a cert
    if score > 0:
        if "IELTS" in doc_type.upper(): db.update_user(tg_id, ielts=score)
        elif "GPA" in doc_type.upper() or "TRANSCRIPT" in doc_type.upper(): db.update_user(tg_id, gpa=score)
    
    verified = 1 if score > 0 else 0
    final_title = user_title if user_title else doc_type
    item_id = db.add_portfolio_item(tg_id, doc_type, final_title, summary_txt, datetime.datetime.now().isoformat()[:10], '', f"/static/uploads/{filename}", verified)
    return jsonify({'ok': True, 'ai_data': ai_data, 'file_url': f"/static/uploads/{filename}"})

# ── BOT INTEGRATION ──
# ── BOT INTEGRATION ──
def start_bot():
    import telebot, os, uuid, json
    TOKEN = os.getenv('TELEGRAM_TOKEN', "8571404835:AAGmgACXxnRU_3jxZV7-Hl4AKIYUX8Ubhg4")
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(commands=['start'])
    def on_start(m):
        import random
        tid = m.from_user.id
        otp = str(random.randint(100000, 999999))
        db.create_user(tid, m.from_user.first_name, m.from_user.username)
        db.update_user(tid, otp=otp)
        
        bot.send_message(m.chat.id, f"🎉 KAIST K-Hub'ga xush kelibsiz!\nSizning kirish kodingiz: `{otp}`\n\nKodni saytga kiriting yoki ushbu havolani bosing:\nhttp://127.0.0.1:5000/auth?token={otp}", parse_mode='Markdown')

    @bot.message_handler(commands=['stats'])
    def on_stats(m):
        u = db.get_user(m.from_user.id)
        if not u: return bot.reply_to(m, "Avval /start bosing!")
        msg = f"📊 *Sizning natijalaringiz (K-HUB)*\n\n👤 Ism: {u['name']}\n📈 Level: {u['level']} ({u['xp']} XP)\n📑 GPA: {u['gpa']}\n🇬🇧 IELTS: {u['ielts']}\n🧪 Research: {u['research']}\n\nBatafsil: http://127.0.0.1:5000/"
        bot.send_message(m.chat.id, msg, parse_mode='Markdown')

    @bot.message_handler(commands=['sop'])
    def on_sop(m):
        bot.send_message(m.chat.id, "✍️ *SOP Lab AI* ishga tushmoqda...\nSiz uchun KAIST talablariga mos SOP draftini tayyorlayapman...", parse_mode='Markdown')
        sop = call_openai_text("Write a 1-paragraph professional SOP intro for a KAIST applicant based on academic excellence. Return only the text.")
        bot.send_message(m.chat.id, f"Mana boshlang'ich qism:\n\n{sop}\n\nTo'liq tahrirlash uchun saytga kiring.")

    @bot.message_handler(commands=['broadcast'])
    def on_broadcast(m):
        u = db.get_user(m.from_user.id)
        if not u or not u.get('is_admin'): return bot.reply_to(m, "Faqat adminlar uchun!")
        text = m.text.replace('/broadcast', '').strip()
        if not text: return bot.reply_to(m, "Xabar matnini kiriting: /broadcast XABAR")
        
        c = db._conn()
        users = c.execute("SELECT tg_id FROM users").fetchall()
        c.close()
        
        count = 0
        for user in users:
            try:
                bot.send_message(user['tg_id'], f"📢 *MUHIM XABAR (K-HUB):*\n\n{text}", parse_mode='Markdown')
                count += 1
            except: pass
        bot.reply_to(m, f"✅ Xabar {count} ta talabaga yuborildi.")

    @bot.message_handler(content_types=['document', 'photo'])
    def handle_docs(m):
        tid = m.from_user.id
        u = db.get_user(tid)
        if not u: return bot.reply_to(m, "Avval /start bosing!")

        bot.send_message(m.chat.id, "🔍 *Hujjat qabul qilindi.* AI tahlil qilmoqda...", parse_mode='Markdown')
        
        try:
            if m.content_type == 'photo':
                file_info = bot.get_file(m.photo[-1].file_id)
                ext = 'jpg'
            else:
                file_info = bot.get_file(m.document.file_id)
                ext = m.document.file_name.rsplit('.', 1)[-1].lower() if '.' in m.document.file_name else 'dat'
            
            downloaded_file = bot.download_file(file_info.file_path)
            f_name = f"{uuid.uuid4()}.{ext}"
            f_path = os.path.join(app.config['UPLOAD_FOLDER'], f_name)
            
            with open(f_path, 'wb') as f:
                f.write(downloaded_file)
            
            # Predict type based on AI if needed, but let's assume it's a generic cert for bot
            res = analyze_document(f_path, "Certificate")
            ai_data = json.loads(res)
            
            score = ai_data.get('score', 0)
            summary = ai_data.get('summary', 'Hujjat tahlil qilindi.')
            
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            db.add_portfolio_item(tid, "Bot Upload", f"Bot: {ext.upper()}", summary, today, '', f"/static/uploads/{f_name}", 0)
            
            bot.send_message(m.chat.id, f"✅ *Tahlil yakunlandi!*\n\n📝 Xulosa: {summary}\n⭐ AI Score: {score}\n\n_Hujjat portfoliongizga 'Unverified' holatida qo'shildi. Admin tasdiqlashini kuting._", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(m.chat.id, f"❌ Xatolik yuz berdi: {str(e)}")

    print("[K-Hub] Bot V2.0 starting...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5, 
                               skip_pending=True, restart_on_change=False)
        except Exception as e:
            err = str(e)
            if "409" in err:
                print("[Bot] 409 Conflict — another instance running. Waiting 15s before retry...")
                import time
                bot.stop_polling()
                time.sleep(15)
                continue
            print(f"[Bot Warning] {err}")
            import time
            time.sleep(5)




if __name__ == '__main__':
    db.init_db()
    # Only start bot once (prevents double-init during Flask reloads)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=start_bot, daemon=True).start()
        
    app.run(port=5000, debug=True)
