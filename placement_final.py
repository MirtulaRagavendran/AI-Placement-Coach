import streamlit as st    
from groq import Groq      
import plotly.graph_objects as go   
import requests     
import PyPDF2                                    
import io   
import json   
import os  
import hashlib       

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))   

st.set_page_config(page_title="AI Placement Coach", page_icon="🎯", layout="centered")    

st.markdown("""  
<style>    
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM Mono&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }   
.stApp { background: #0d0f1a; color: #e8eaf6; }   
.hero {   
    background: linear-gradient(135deg,#1a1d35,#12162b);   
    border: 1px solid #2a2f5a; border-radius: 18px;    
    padding: 2rem 2.4rem 1.6rem; margin-bottom: 2rem;    
}    
.hero h1 { font-size:2rem; font-weight:800; color:#e8eaf6; margin:0 0 .3rem; }   
.hero p  { color:#7b82b8; font-family:'DM Mono',monospace; font-size:.9rem; margin:0; }  
.section-label {   
    font-size:.72rem; font-weight:700; letter-spacing:2px;   
    text-transform:uppercase; color:#5c63a8; margin-bottom:.8rem;  
}  
.score-card { border-radius:16px; padding:1.8rem 2rem; text-align:center; margin:1.2rem 0; border:1px solid; }
.score-card.mnc      { background:linear-gradient(135deg,#0f2a1a,#0d1f28); border-color:#22c55e; box-shadow:0 0 30px rgba(34,197,94,.15); }
.score-card.improve  { background:linear-gradient(135deg,#2a1f0a,#1f1a0d); border-color:#f59e0b; box-shadow:0 0 30px rgba(245,158,11,.15); }
.score-card.beginner { background:linear-gradient(135deg,#2a0d0d,#1a0d1f); border-color:#ef4444; box-shadow:0 0 30px rgba(239,68,68,.15); }
.score-card .badge        { font-size:2.8rem; margin-bottom:.3rem; }
.score-card .status-text  { font-size:1.5rem; font-weight:800; }
.score-card.mnc .status-text      { color:#4ade80; }
.score-card.improve .status-text  { color:#fbbf24; }
.score-card.beginner .status-text { color:#f87171; }
.score-card .score-num { font-family:'DM Mono',monospace; font-size:3.5rem; font-weight:700; line-height:1; margin:.5rem 0 .2rem; }
.score-card.mnc .score-num      { color:#22c55e; }
.score-card.improve .score-num  { color:#f59e0b; }
.score-card.beginner .score-num { color:#ef4444; }
.score-card .score-label { font-size:.75rem; letter-spacing:2px; text-transform:uppercase; color:#5c63a8; font-family:'DM Mono',monospace; }
.profile-card {
    background:#12162b; border:1px solid #2a2f5a;
    border-radius:14px; padding:1.4rem 1.6rem; margin-bottom:1rem;
}
.profile-card h3 { color:#e8eaf6; margin:0 0 .5rem; font-size:1.2rem; }
.profile-card p  { color:#7b82b8; margin:.2rem 0; font-size:.9rem; font-family:'DM Mono',monospace; }
.ai-box {
    background:#12162b; border:1px solid #2a2f5a;
    border-radius:14px; padding:1.4rem 1.6rem;
    margin-top:1rem; font-size:.9rem; color:#c5c9e8; line-height:1.8;
}
.leet-box {
    background:#12162b; border:1px solid #6366f1;
    border-radius:14px; padding:1.2rem 1.4rem; margin-top:1rem; font-size:.9rem; color:#c5c9e8;
}
.interview-q {
    background:#12162b; border:1px solid #f59e0b;
    border-radius:14px; padding:1.2rem 1.4rem;
    margin-bottom:1rem; font-size:.95rem; color:#e8eaf6; font-weight:700;
}
.company-card {
    background:#12162b; border:1px solid #2a2f5a;
    border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:1rem;
}
.company-card h4 { color:#e8eaf6; margin:0 0 .4rem; font-size:1rem; }
.company-card p  { color:#7b82b8; margin:0; font-size:.85rem; }
.apt-question {
    background:#12162b; border:1px solid #6366f1;
    border-radius:14px; padding:1.2rem 1.4rem; margin-bottom:1rem;
}
.apt-question h4 { color:#e8eaf6; margin:0 0 .8rem; font-size:1rem; }
.score-badge-green { color:#4ade80; font-weight:800; font-size:1.2rem; }
.score-badge-red   { color:#f87171; font-weight:800; font-size:1.2rem; }
hr { border-color:#1e2244; }
</style>
""", unsafe_allow_html=True)

# ── User Database ─────────────────────────────────────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f: 
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ── Session State ─────────────────────────────────────────────────────────────
defaults = {
    "logged_in": False,
    "current_user": None,
    "interview_question": "",
    "interview_started": False,
    "apt_questions": [],
    "apt_answers": {},
    "apt_score": None,
    "apt_submitted": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTER 
# ════════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
                
<svg width="100%" viewBox="0 0 680 120" xmlns="http://www.w3.org/2000/svg">
<circle cx="60" cy="60" r="38" fill="none" stroke="#6366f1" stroke-width="2.5"/>
<circle cx="60" cy="60" r="25" fill="none" stroke="#818cf8" stroke-width="2.5"/>
<circle cx="60" cy="60" r="12" fill="none" stroke="#c7d2fe" stroke-width="2.5"/>
<circle cx="60" cy="60" r="5" fill="#22c55e"/>
<line x1="60" y1="22" x2="60" y2="34" stroke="#6366f1" stroke-width="1.5"/>
<line x1="60" y1="86" x2="60" y2="98" stroke="#6366f1" stroke-width="1.5"/>
<line x1="22" y1="60" x2="34" y2="60" stroke="#6366f1" stroke-width="1.5"/>
<line x1="86" y1="60" x2="98" y2="60" stroke="#6366f1" stroke-width="1.5"/>
<text x="115" y="52" font-family="Arial" font-size="26" font-weight="800" fill="#e8eaf6">AI Placement Coach</text>
<text x="117" y="74" font-family="Arial" font-size="12" fill="#7b82b8">// Your Personal Placement Trainer</text>
</svg>
      <h1>🎯 AI Placement Coach</h1>
      <p>//· Your Personal Placement Trainer</p>
    </div>
    """, unsafe_allow_html=True)

    auth1, auth2 = st.tabs(["🔐 Login", "📝 Register"])

    with auth1:
        st.markdown('<div class="section-label">Login to your account</div>', unsafe_allow_html=True)
        lu = st.text_input("Username", key="lu")
        lp = st.text_input("Password", type="password", key="lp")
        if st.button("🚀 Login", use_container_width=True):
            users = load_users()
            if lu in users and users[lu]["password"] == hash_password(lp):
                st.session_state.logged_in = True
                st.session_state.current_user = lu
                st.rerun()
            else:
                st.error("❌ Wrong username or password!")

    with auth2:
        st.markdown('<div class="section-label">Create new account</div>', unsafe_allow_html=True)
        rname    = st.text_input("Full Name", placeholder="e.g. Arjun Kumar")
        rcollege = st.text_input("College Name", placeholder="e.g. Anna University")
        rdept    = st.text_input("Department", placeholder="e.g. CSE")
        ryear    = st.selectbox("Year", ["1st Year","2nd Year","3rd Year","4th Year"])
        ruser    = st.text_input("Username", placeholder="e.g. arjun123")
        rpass    = st.text_input("Password", type="password", key="rp1")
        rpass2   = st.text_input("Confirm Password", type="password", key="rp2")
        if st.button("✅ Register", use_container_width=True):
            if not all([rname, rcollege, rdept, ruser, rpass]):
                st.error("❌ Fill all fields!")
            elif rpass != rpass2:
                st.error("❌ Passwords don't match!")
            else:
                users = load_users()
                if ruser in users:
                    st.error("❌ Username taken!")
                else:
                    users[ruser] = {
                        "name": rname, "college": rcollege,
                        "dept": rdept, "year": ryear,
                        "password": hash_password(rpass),
                        "dsa_progress": {},
                        "aptitude_score": 0
                    }
                    save_users(users)
                    st.success("✅ Registered! Please login.")

# ════════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════════
else:
    users = load_users()
    ud = users.get(st.session_state.current_user, {})

    col_h, col_l = st.columns([4,1])
    with col_h:
        st.markdown(f"""
        <div class="hero">
          <h1>🎯 AI Placement Coach</h1>
          <p>// Welcome, {ud.get('name','Student')} · {ud.get('college','')} · {ud.get('dept','')} · {ud.get('year','')}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_l:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
        "📊 Dashboard",
        "👤 Profile",
        "🧮 Aptitude Test",
        "📅 Study Planner",
        "📝 DSA Tracker",
        "🏢 Company Prep",
        "📄 Resume",
        "🎤 Interview"
    ])

    # ── TAB 1: DASHBOARD ──────────────────────────────────────────────────────
    with tab1:
        # Saved aptitude score
        saved_apt = ud.get("aptitude_score", 0)

        st.markdown('<div class="section-label">⚡ LeetCode Auto Fetch</div>', unsafe_allow_html=True)
        lc1,lc2 = st.columns([3,1])
        with lc1:
            username = st.text_input("LeetCode Username", placeholder="e.g. john_doe")
        with lc2:
            fetch_btn = st.button("🔍 Fetch", use_container_width=True)

        leetcode = 0
        if fetch_btn and username:
            with st.spinner("Fetching from LeetCode..."):
                try:
                    query = """query getUserProfile($username: String!) {
                        matchedUser(username: $username) {
                            submitStats { acSubmissionNum { difficulty count } }
                        }
                    }"""
                    resp = requests.post(
                        "https://leetcode.com/graphql",
                        json={"query": query, "variables": {"username": username}},
                        headers={"Content-Type": "application/json"}, timeout=10
                    )
                    data = resp.json()
                    user_lc = data.get("data", {}).get("matchedUser")
                    if user_lc:
                        stats = user_lc["submitStats"]["acSubmissionNum"]
                        total = next((s["count"] for s in stats if s["difficulty"] == "All"), 0)
                        leetcode = min(total, 500)
                        st.markdown(f'<div class="leet-box">✅ <b>{username}</b> — <b>{total} problems solved!</b></div>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Username not found!")
                except:
                    st.error("❌ Could not connect. Enter manually below.")

        st.markdown("---")
        st.markdown('<div class="section-label">📥 Your Stats</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: leetcode  = st.slider("LeetCode Problems", 0, 500, leetcode, 5)
        with c2: cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=7.5, step=0.1)
        with c3:
            aptitude = st.slider("Aptitude Score", 0, 100, saved_apt, 1)
            if saved_apt > 0:
                st.caption(f"✅ Auto-filled from your last test: {saved_apt}/100")

        leet_norm = (leetcode/500)*100
        cgpa_norm = (cgpa/10)*100
        apt_norm  = float(aptitude)
        weighted_score = round(leet_norm*0.4 + cgpa_norm*0.3 + apt_norm*0.3, 1)

        if weighted_score >= 72:
            status, card_class, badge = "Ready for MNC", "mnc", "🚀"
        elif weighted_score >= 45:
            status, card_class, badge = "Needs Improvement", "improve", "⚡"
        else:
            status, card_class, badge = "Beginner", "beginner", "🌱"

        st.markdown("---")
        st.markdown(f"""
        <div class="score-card {card_class}">
          <div class="badge">{badge}</div>
          <div class="status-text">{status}</div>
          <div class="score-num">{weighted_score}</div>
          <div class="score-label">Weighted Score / 100</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["LeetCode (40%)", "CGPA (30%)", "Aptitude (30%)"],
            y=[round(leet_norm,1), round(cgpa_norm,1), round(apt_norm,1)],
            marker_color=["#6366f1","#22d3ee","#f59e0b"],
            text=[f"{leetcode}/500", f"{cgpa}/10", f"{aptitude}/100"],
            textposition="outside",
            textfont=dict(color="#e8eaf6", family="DM Mono", size=14),
        ))
        fig.add_hline(y=72, line_dash="dot", line_color="#22c55e", line_width=1.5,
            annotation_text="MNC Threshold (72)", annotation_font_color="#22c55e",
            annotation_position="top right")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,15,26,0.6)",
            font=dict(family="Syne", color="#9da5d4"),
            yaxis=dict(range=[0,115], gridcolor="#1e2244"),
            margin=dict(l=10,r=10,t=30,b=10), showlegend=False, height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        if st.button("🤖 Get AI Analysis!", use_container_width=True, key="ai_dash"):
            with st.spinner("AI is thinking..."):
                r = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role":"user","content":f"""
You are an expert placement coach for Indian CSE students.
Student: {ud.get('name')}, {ud.get('college')}, {ud.get('dept')}, {ud.get('year')}
LeetCode: {leetcode}/500 | CGPA: {cgpa}/10 | Aptitude: {aptitude}/100 | Score: {weighted_score}/100 | Status: {status}
Give personalized placement roadmap:
1. 3 weak areas to improve
2. Top 5 suitable companies right now
3. 3 DSA topics to focus immediately
4. 2 mock interview questions with answers
5. 30-day action plan
Be practical, specific, motivating. Format with clear headings.
"""}])
                st.markdown(f'<div class="ai-box">{r.choices[0].message.content}</div>', unsafe_allow_html=True)

    # ── TAB 2: PROFILE ────────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-label">👤 My Profile</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="profile-card">
          <h3>👤 {ud.get('name','Student')}</h3>
          <p>🏫 {ud.get('college','-')}</p>
          <p>📚 {ud.get('dept','-')} · {ud.get('year','-')}</p>
          <p>🎯 Last Aptitude Score: {ud.get('aptitude_score', 0)}/100</p>
          <p>🔑 @{st.session_state.current_user}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-label">✏️ Update Profile</div>', unsafe_allow_html=True)
        nn = st.text_input("Full Name",   value=ud.get('name',''))
        nc = st.text_input("College",     value=ud.get('college',''))
        nd = st.text_input("Department",  value=ud.get('dept',''))
        ny = st.selectbox("Year", ["1st Year","2nd Year","3rd Year","4th Year"],
             index=["1st Year","2nd Year","3rd Year","4th Year"].index(ud.get('year','1st Year')))
        if st.button("💾 Save Profile", use_container_width=True):
            users = load_users()
            users[st.session_state.current_user].update({"name":nn,"college":nc,"dept":nd,"year":ny})
            save_users(users)
            st.success("✅ Profile updated!")
            st.rerun()

    # ── TAB 3: APTITUDE TEST ──────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-label">🧮 Aptitude Mock Test</div>', unsafe_allow_html=True)
        st.write("10 questions — AI generates — you answer — score auto-saved to Dashboard!")

        apt_type = st.selectbox("Test Type", [
            "Mixed (Quant + Logical + Verbal)",
            "Quantitative Aptitude only",
            "Logical Reasoning only",
            "Verbal Ability only"
        ])

        if st.button("🎯 Generate Test!", use_container_width=True) and not st.session_state.apt_submitted:
            with st.spinner("AI generating 10 questions..."):
                q_prompt = f"""
Generate exactly 10 multiple choice aptitude questions for Indian placement exams ({apt_type}).
Each question must have 4 options and one correct answer.

Return ONLY a valid JSON array like this:
[
  {{
    "q": "Question text here?",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "answer": "A) option1"
  }}
]
No extra text, no markdown, just the JSON array.
"""
                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":q_prompt}]
                )
                try:
                    raw = r.choices[0].message.content.strip()
                    raw = raw.replace("```json","").replace("```","").strip()
                    questions = json.loads(raw)
                    st.session_state.apt_questions = questions
                    st.session_state.apt_answers = {}
                    st.session_state.apt_score = None
                    st.session_state.apt_submitted = False
                except:
                    st.error("❌ Error generating questions. Try again!")

        # Show questions
        if st.session_state.apt_questions and not st.session_state.apt_submitted:
            st.markdown("---")
            for i, q in enumerate(st.session_state.apt_questions):
                st.markdown(f'<div class="apt-question"><h4>Q{i+1}. {q["q"]}</h4></div>', unsafe_allow_html=True)
                selected = st.radio(
                    f"Select answer for Q{i+1}:",
                    q["options"],
                    key=f"apt_q_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.apt_answers[i] = selected
                st.markdown("---")

            if len(st.session_state.apt_answers) == len(st.session_state.apt_questions):
                if st.button("✅ Submit Test!", use_container_width=True):
                    correct = 0
                    for i, q in enumerate(st.session_state.apt_questions):
                        if st.session_state.apt_answers.get(i) == q["answer"]:
                            correct += 1
                    score = int((correct / len(st.session_state.apt_questions)) * 100)
                    st.session_state.apt_score = score
                    st.session_state.apt_submitted = True

                    # Save to user profile
                    users = load_users()
                    users[st.session_state.current_user]["aptitude_score"] = score
                    save_users(users)
                    st.rerun()

        # Show results
        if st.session_state.apt_submitted and st.session_state.apt_score is not None:
            score = st.session_state.apt_score
            correct = sum(1 for i,q in enumerate(st.session_state.apt_questions)
                         if st.session_state.apt_answers.get(i) == q["answer"])

            if score >= 70:
                sc, sc_class = "mnc", "🎉 Excellent!"
            elif score >= 45:
                sc, sc_class = "improve", "👍 Good effort!"
            else:
                sc, sc_class = "beginner", "💪 Keep practicing!"

            st.markdown(f"""
            <div class="score-card {sc}">
              <div class="badge">🧮</div>
              <div class="status-text">{sc_class}</div>
              <div class="score-num">{score}</div>
              <div class="score-label">Aptitude Score / 100 · {correct}/10 Correct · Auto-saved to Dashboard ✅</div>
            </div>
            """, unsafe_allow_html=True)

            # Show correct/wrong answers
            st.markdown("---")
            st.markdown('<div class="section-label">📋 Answer Review</div>', unsafe_allow_html=True)
            for i, q in enumerate(st.session_state.apt_questions):
                user_ans = st.session_state.apt_answers.get(i, "")
                correct_ans = q["answer"]  
                is_correct = user_ans == correct_ans
                icon = "✅" if is_correct else "❌"
                st.markdown(f"""
                <div class="apt-question">
                  <h4>{icon} Q{i+1}. {q["q"]}</h4>
                  <p style="color:{'#4ade80' if is_correct else '#f87171'}">Your answer: {user_ans}</p>
                  {"" if is_correct else f'<p style="color:#4ade80">Correct answer: {correct_ans}</p>'}
                </div>
                """, unsafe_allow_html=True)

            if st.button("🔄 Take New Test", use_container_width=True):
                st.session_state.apt_questions = []
                st.session_state.apt_answers = {}
                st.session_state.apt_score = None
                st.session_state.apt_submitted = False
                st.rerun()   

    # ── TAB 4: STUDY PLANNER ──────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-label">📅 AI Daily Study Planner</div>', unsafe_allow_html=True)
        st.write("Tell AI your situation — get a personalized day-by-day study plan!")

        p1,p2 = st.columns(2)
        with p1:
            days_left   = st.number_input("Days until placement?", min_value=7, max_value=365, value=30)
            daily_hours = st.number_input("Hours available per day?", min_value=1, max_value=12, value=4)
        with p2:
            weak_areas = st.multiselect("Weak areas?",
                ["Arrays","Strings","Trees","Graphs","DP","SQL","OS","DBMS",
                 "System Design","Aptitude","Communication","HR Questions"])
            target_company = st.selectbox("Target company?",
                ["Any MNC","TCS/Infosys/Wipro","Zoho/Freshworks","Amazon/Google","Startups"])

        if st.button("📅 Generate My Study Plan!", use_container_width=True):
            with st.spinner("AI creating your plan..."):
                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":f"""
You are an expert placement coach for Indian CSE students.
Student: {ud.get('name')}, {ud.get('year')}
Days until placement: {days_left} | Daily hours: {daily_hours}
Weak areas: {', '.join(weak_areas) if weak_areas else 'Not specified'}
Target: {target_company}

Create detailed day-by-day study plan for {min(days_left,30)} days.
Format: Week 1: [Theme] → Day 1: [Topic] - [Tasks] - [Resources]
Include morning DSA, afternoon theory, evening mock tests.
Be very specific with topics and YouTube channels.
"""}])
                st.markdown(f'<div class="ai-box">{r.choices[0].message.content}</div>', unsafe_allow_html=True)

    # ── TAB 5: DSA TRACKER ────────────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="section-label">📝 DSA Topic Tracker</div>', unsafe_allow_html=True)
        st.write("Track which topics you've completed!")

        dsa_topics = {
    "Arrays & Strings": [
        {"topic": "Two Pointers", "yt": "https://youtu.be/On03HWe2tZM", "lc": "https://leetcode.com/problems/two-sum/"},
        {"topic": "Sliding Window", "yt": "https://youtu.be/MK-NZ4hN7rs", "lc": "https://leetcode.com/problems/longest-substring-without-repeating-characters/"},
        {"topic": "Kadane's Algorithm", "yt": "https://youtu.be/86CQq3pKSUw", "lc": "https://leetcode.com/problems/maximum-subarray/"},
        {"topic": "Binary Search on Array", "yt": "https://youtu.be/GU7DpgHINWQ", "lc": "https://leetcode.com/problems/binary-search/"},
    ],
    "Linked List": [
        {"topic": "Reverse LL", "yt": "https://youtu.be/G0_I-ZF0S38", "lc": "https://leetcode.com/problems/reverse-linked-list/"},
        {"topic": "Detect Cycle", "yt": "https://youtu.be/wiOo4DC5GGA", "lc": "https://leetcode.com/problems/linked-list-cycle/"},
        {"topic": "Merge Two Sorted LL", "yt": "https://youtu.be/XIdigk956u0", "lc": "https://leetcode.com/problems/merge-two-sorted-lists/"},
        {"topic": "Find Middle", "yt": "https://youtu.be/7LjQ57RqgEc", "lc": "https://leetcode.com/problems/middle-of-the-linked-list/"},
    ],
    "Trees": [
        {"topic": "BFS/DFS", "yt": "https://youtu.be/pcKY4hjDrxk", "lc": "https://leetcode.com/problems/binary-tree-level-order-traversal/"},
        {"topic": "Binary Search Tree", "yt": "https://youtu.be/pYT9F8_LFTM", "lc": "https://leetcode.com/problems/validate-binary-search-tree/"},
        {"topic": "Height of Tree", "yt": "https://youtu.be/aqLTbtWh40E", "lc": "https://leetcode.com/problems/maximum-depth-of-binary-tree/"},
        {"topic": "LCA", "yt": "https://youtu.be/_-QHfMDde90", "lc": "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/"},
    ],
    "Graphs": [
        {"topic": "BFS", "yt": "https://youtu.be/oDqjPvD54Ss", "lc": "https://leetcode.com/problems/number-of-islands/"},
        {"topic": "DFS", "yt": "https://youtu.be/7fujbpJ0LB4", "lc": "https://leetcode.com/problems/max-area-of-island/"},
        {"topic": "Dijkstra", "yt": "https://youtu.be/XB4MIexjvY0", "lc": "https://leetcode.com/problems/network-delay-time/"},
        {"topic": "Topological Sort", "yt": "https://youtu.be/eL10SBdfwmA", "lc": "https://leetcode.com/problems/course-schedule/"},
    ],
    "Dynamic Programming": [
        {"topic": "Fibonacci", "yt": "https://youtu.be/vYquumk4nXw", "lc": "https://leetcode.com/problems/fibonacci-number/"},
        {"topic": "0/1 Knapsack", "yt": "https://youtu.be/8LusJS5-AGo", "lc": "https://leetcode.com/problems/partition-equal-subset-sum/"},
        {"topic": "LCS", "yt": "https://youtu.be/sSno9rV8Rhg", "lc": "https://leetcode.com/problems/longest-common-subsequence/"},
        {"topic": "LIS", "yt": "https://youtu.be/CE2b_-XfVDk", "lc": "https://leetcode.com/problems/longest-increasing-subsequence/"},
    ],
    "Sorting & Searching": [
        {"topic": "Quick Sort", "yt": "https://youtu.be/COk73cpQbFQ", "lc": "https://leetcode.com/problems/sort-an-array/"},
        {"topic": "Merge Sort", "yt": "https://youtu.be/JSceec-wEyw", "lc": "https://leetcode.com/problems/sort-an-array/"},
        {"topic": "Binary Search", "yt": "https://youtu.be/GU7DpgHINWQ", "lc": "https://leetcode.com/problems/binary-search/"},
        {"topic": "Count Sort", "yt": "https://youtu.be/7zuGmKfUt7s", "lc": "https://leetcode.com/problems/sort-colors/"},
    ],
    "Stack & Queue": [
        {"topic": "Valid Parentheses", "yt": "https://youtu.be/WTzjTskDFMg", "lc": "https://leetcode.com/problems/valid-parentheses/"},
        {"topic": "Next Greater Element", "yt": "https://youtu.be/Du881K7Jtk8", "lc": "https://leetcode.com/problems/next-greater-element-i/"},
        {"topic": "Implement Queue using Stack", "yt": "https://youtu.be/3Et9MrMc02A", "lc": "https://leetcode.com/problems/implement-queue-using-stacks/"},
    ],
    "SQL & DBMS": [
        {"topic": "Joins", "yt": "https://youtu.be/9yeOJ0ZMUYw", "lc": "https://leetcode.com/problems/combine-two-tables/"},
        {"topic": "Subqueries", "yt": "https://youtu.be/nMIjDUMboHE", "lc": "https://leetcode.com/problems/employees-earning-more-than-their-managers/"},
        {"topic": "Indexes", "yt": "https://youtu.be/fsG1XaZEa78", "lc": "https://leetcode.com/problems/find-customer-referee/"},
        {"topic": "Normalization", "yt": "https://youtu.be/GFQaEYEc8_8", "lc": "https://leetcode.com/problems/second-highest-salary/"},
    ],
    "OS Concepts": [
        {"topic": "Process vs Thread", "yt": "https://youtu.be/exbKr6fnoUw", "lc": "https://leetcode.com/discuss/general-discussion/1059074/os-concepts"},
        {"topic": "Deadlock", "yt": "https://youtu.be/UVo9mGARkhQ", "lc": "https://leetcode.com/discuss/general-discussion/1059074/os-concepts"},
        {"topic": "Paging", "yt": "https://youtu.be/pJ6qrCB8pDw", "lc": "https://leetcode.com/discuss/general-discussion/1059074/os-concepts"},
        {"topic": "Scheduling", "yt": "https://youtu.be/Jkmy2YLUbUY", "lc": "https://leetcode.com/discuss/general-discussion/1059074/os-concepts"},
    ],
}
        users = load_users()
        progress = users.get(st.session_state.current_user, {}).get("dsa_progress", {})
        total_topics = sum(len(v) for v in dsa_topics.values())
        done_topics  = sum(1 for cat in dsa_topics for t in dsa_topics[cat] if progress.get(f"{cat}_{t['topic']}", False))

        st.progress(done_topics/total_topics)
        st.markdown(f"**{done_topics}/{total_topics} topics completed ({int((done_topics/total_topics)*100)}%)**")
        st.markdown("---")

        changed = False
        new_progress = dict(progress)

        for category, topics in dsa_topics.items():
            done_in_cat = sum(1 for t in topics if progress.get(f"{category}_{t['topic']}", False))
            with st.expander(f"📁 {category} ({done_in_cat}/{len(topics)} done)"):
                for item in topics:
                    topic = item["topic"]
                    key = f"{category}_{topic}"
                    col_chk, col_yt, col_lc = st.columns([3, 1, 1])
                    with col_chk:
                        checked = st.checkbox(topic, value=progress.get(key, False), key=f"chk_{key}")
                    with col_yt:
                        st.markdown(f"[📹 Watch]({item['yt']})")
                    with col_lc:
                        st.markdown(f"[💻 Practice]({item['lc']})")
                    if checked != progress.get(key, False):
                        new_progress[key] = checked
                        changed = True

        if changed:
            users = load_users()
            if "dsa_progress" not in users[st.session_state.current_user]:
                users[st.session_state.current_user]["dsa_progress"] = {}
            users[st.session_state.current_user]["dsa_progress"] = new_progress
            save_users(users)
            st.rerun()

            topic = item["topic"]
            key = f"{category}_{topic}"
            col_chk, col_yt, col_lc = st.columns([3, 1, 1])
            with col_chk:
                checked = st.checkbox(topic, value=progress.get(key, False), key=f"chk_{key}")
            with col_yt:
                st.markdown(f"[📹 Watch]({item['yt']})")
            with col_lc:
                st.markdown(f"[💻 Practice]({item['lc']})")
            if checked != progress.get(key, False):
                users = load_users()
                if "dsa_progress" not in users[st.session_state.current_user]:
                    users[st.session_state.current_user]["dsa_progress"] = {}
                users[st.session_state.current_user]["dsa_progress"][key] = checked
                save_users(users)
                st.rerun()

    # ── TAB 6: COMPANY PREP ───────────────────────────────────────────────────
    with tab6:
        st.markdown('<div class="section-label">🏢 Company-wise Preparation</div>', unsafe_allow_html=True)
        st.write("Select a company — AI gives exact preparation strategy!")

        companies = {
            "TCS":        {"package":"3.5-4 LPA",   "difficulty":"Easy"},
            "Infosys":    {"package":"3.6-4 LPA",   "difficulty":"Easy-Medium"},
            "Wipro":      {"package":"3.5 LPA",     "difficulty":"Easy"},
            "Cognizant":  {"package":"4-4.5 LPA",   "difficulty":"Easy-Medium"},
            "Zoho":       {"package":"5-8 LPA",     "difficulty":"Medium-Hard"},
            "Freshworks": {"package":"8-12 LPA",    "difficulty":"Hard"},
            "Amazon":     {"package":"15-25 LPA",   "difficulty":"Very Hard"},
            "Google":     {"package":"25-40 LPA",   "difficulty":"Very Hard"},
        }

        cols = st.columns(4)
        for i, (company, info) in enumerate(companies.items()):
            with cols[i%4]:
                st.markdown(f"""
                <div class="company-card">
                  <h4>{company}</h4>
                  <p>💰 {info['package']}</p>
                  <p>📊 {info['difficulty']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        selected = st.selectbox("Select Company:", list(companies.keys()))

        if st.button(f"🤖 Get {selected} Prep Strategy!", use_container_width=True):
            with st.spinner(f"Preparing {selected} strategy..."):
                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":f"""
Expert placement coach for Indian MNC recruitment.
Student: {ud.get('name')}, {ud.get('year')} CSE | Target: {selected} ({companies[selected]['package']})
Provide complete prep strategy:
1. All recruitment rounds explained
2. Technical topics with priority
3. Top 10 most asked questions
4. Aptitude topics specific to {selected}
5. HR questions they always ask
6. Coding platform tips
7. 2-week specific prep plan
8. Do's and Don'ts
Be very specific to {selected}'s actual process.
"""}])
                st.markdown(f'<div class="ai-box">{r.choices[0].message.content}</div>', unsafe_allow_html=True)

    # ── TAB 7: RESUME ─────────────────────────────────────────────────────────
    with tab7:
        st.markdown('<div class="section-label">📄 Resume Analyzer</div>', unsafe_allow_html=True)
        st.write("Upload your resume — AI analyzes strengths & weaknesses!")
        uploaded = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        if uploaded:
            with st.spinner("Reading resume..."):
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(uploaded.read()))
                    text = "".join(p.extract_text() for p in reader.pages)
                    if text.strip():
                        st.success("✅ Resume read successfully!")
                        if st.button("🤖 Analyze Resume!", use_container_width=True):
                            with st.spinner("AI analyzing..."):
                                r = client.chat.completions.create(
                                    model="llama-3.3-70b-versatile",
                                    messages=[{"role":"user","content":f"""
Analyze CSE student resume for placement readiness:
{text[:3000]}
Provide:
1. Top 3 Strengths
2. Top 3 Weaknesses / Missing sections
3. Skills to add immediately
4. ATS Score out of 100 with reason
5. Line-by-line improvements for MNC-readiness
Be specific and constructive.
"""}])
                                st.markdown(f'<div class="ai-box">{r.choices[0].message.content}</div>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Could not read PDF.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # ── TAB 8: MOCK INTERVIEW ─────────────────────────────────────────────────
    with tab8:
        st.markdown('<div class="section-label">🎤 Mock Interview Mode</div>', unsafe_allow_html=True)
        st.write("AI asks questions — you answer — AI evaluates you!")
        ca,cb = st.columns(2)
        with ca: itype = st.selectbox("Type", ["DSA","HR","System Design","DBMS","OS","Aptitude"])
        with cb: idiff = st.selectbox("Difficulty", ["Easy","Medium","Hard"])

        if st.button("🎯 Start Interview!", use_container_width=True):
            with st.spinner("Preparing question..."):
                q = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":f"Generate ONE {idiff} {itype} interview question for a CSE fresher applying to Indian MNCs. Just the question, no extra text."}]
                )
                st.session_state.interview_question = q.choices[0].message.content
                st.session_state.interview_started = True

        if st.session_state.interview_started and st.session_state.interview_question:
            st.markdown(f'<div class="interview-q">❓ {st.session_state.interview_question}</div>', unsafe_allow_html=True)
            answer = st.text_area("Your Answer:", height=150, placeholder="Type your answer here...")
            if st.button("✅ Submit Answer", use_container_width=True):
                if answer.strip():
                    with st.spinner("Evaluating..."):
                        ev = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role":"user","content":f"""
Evaluate CSE fresher's interview answer for Indian MNC:
Question: {st.session_state.interview_question}
Answer: {answer}
Provide: 1) Score/10  2) What was good  3) What was missing  4) Ideal answer  5) Tips to improve
"""}])
                        st.markdown(f'<div class="ai-box">{ev.choices[0].message.content}</div>', unsafe_allow_html=True)
                else:
                    st.warning("Please type your answer first!")

    st.caption("Built with ❤️ for placement training · Powered by Groq AI + Streamlit")  
