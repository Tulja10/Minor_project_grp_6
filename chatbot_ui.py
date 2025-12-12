import os
import time
import requests
import streamlit as st

# ---------------------- Page config ----------------------
st.set_page_config(page_title="Student FAQ Chatbot", page_icon="🤖", layout="wide")

# ---------------------- Dark styling ----------------------
st.markdown(
    """
    <style>
    /* Full app dark background and light text */
    .stApp {
        background-color: #020617;  /* almost black */
        color: #e5e7eb;             /* slate-100 */
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
    }

    /* Sidebar dark background */
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
        color: #e5e7eb !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #f9fafb !important;
    }

    /* Chat card container */
    .chat-card {
        background: #020617;
        padding: 1.2rem 1.5rem;
        border-radius: 18px;
        border: 1px solid #1f2937;
        box-shadow: none;
    }

    .small-muted {
        font-size: 0.85rem;
        color: #9ca3af;
    }

    .pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        background: #1f2937;
        color: #93c5fd;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-right: 0.3rem;
    }

    /* Chat messages: ensure text is bright */
    [data-testid="stChatMessage"] p {
        color: #e5e7eb !important;
    }

    .stButton>button {
        border-radius: 999px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------- Configuration ----------------------
BACKEND_URL_SEARCH = os.environ.get("FAQ_BACKEND_URL", "http://127.0.0.1:5000/search")
USERDB_LOG_URL = os.environ.get("FAQ_USERDB_LOG_URL", None)

USE_LLM_POST_PROCESS = False  # set True when you plug in an LLM endpoint
LLM_BACKEND_URL = os.environ.get("FAQ_LLM_URL", None)

HISTORY_TURNS = 6

# Sample hard-coded user with personal data
SAMPLE_USER = {
    "name": "Yuvanshi Bhalawat",
    "email": "yuvanshibhalawat@acropolis.in",
    "branch": "IT",
    "attendance": "85%",
    "cgpa": "8.5",
}

# ---------------------- State initialization ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None  # simple session-based "login id" (email)
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None  # "login" or "signup" or None
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}  # in-memory profile for this session
if "registered_users" not in st.session_state:
    # simple in-memory "database" of registered users, keyed by email (lowercase)
    st.session_state.registered_users = {}


# ---------------------- Helpers ----------------------
def append_message(role: str, content: str) -> None:
    st.session_state.messages.append(
        {"role": role, "content": content, "ts": time.time()}
    )


def get_recent_history(n_turns: int = HISTORY_TURNS):
    if not st.session_state.messages:
        return []
    recent = st.session_state.messages[-(n_turns * 2):]
    return [{"role": m["role"], "content": m["content"]} for m in recent]


def call_backend_search(query: str, timeout: int = 20) -> str:
    payload = {"query": query}
    try:
        res = requests.post(BACKEND_URL_SEARCH, json=payload, timeout=timeout)
    except requests.RequestException as e:
        return f"❌ Error contacting backend: {e}"

    if not res.ok:
        return f"❌ Backend error {res.status_code}: {res.text}"

    try:
        data = res.json()
    except Exception:
        return res.text or ""

    return str(data.get("answer", ""))


def personalize_answer(query: str, base_answer: str) -> str:
    """
    If the logged-in user is the sample user and question is about attendance or result,
    override the generic answer with personalized data.
    """
    profile = st.session_state.user_profile or {}
    email = profile.get("email") or st.session_state.user_id

    if email and email.lower() == SAMPLE_USER["email"].lower():
        q = query.lower()
        if "attendance" in q:
            return f"Your current attendance is **{SAMPLE_USER['attendance']}**."
        if "result" in q or "cgpa" in q or "c.g.p.a" in q:
            return f"Your current result is **{SAMPLE_USER['cgpa']} CGPA**."

    return base_answer


def call_llm_post_process(query: str, answer: str, history=None, timeout: int = 20) -> str:
    """Optional LLM refinement hook. Currently returns the original answer."""
    if not USE_LLM_POST_PROCESS or not LLM_BACKEND_URL:
        return answer

    payload = {"query": query, "answer": answer}
    if history:
        payload["history"] = history

    try:
        res = requests.post(LLM_BACKEND_URL, json=payload, timeout=timeout)
    except requests.RequestException as e:
        return f"{answer}\n\n(LLM error: {e})"

    if not res.ok:
        return f"{answer}\n\n(LLM backend error {res.status_code}: {res.text})"

    try:
        data = res.json()
    except Exception:
        return answer

    return str(data.get("answer", answer))


def pick_emoji(query: str, answer: str) -> str:
    """Pick an emoji based on the tone of the query."""
    q = query.lower()
    if any(w in q for w in ["thank", "thanks", "thanku", "thx"]):
        return "😊"
    if any(w in q for w in ["sorry", "confused", "doubt"]):
        return "😅"
    if "?" in q or any(w in q for w in ["how", "what", "why", "when", "where"]):
        return "🤔"
    if any(w in q for w in ["great", "awesome", "nice", "good"]):
        return "😄"
    return "🤖"


def log_chat_event(user_id, question, answer, ts=None):
    """Optional logging to external user DB (noop if USERDB_LOG_URL is not set)."""
    if not USERDB_LOG_URL:
        return

    payload = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "timestamp": ts or time.time(),
        "meta": {"source": "faq_vector_db"},
    }
    try:
        requests.post(USERDB_LOG_URL, json=payload, timeout=5)
    except requests.RequestException:
        pass


def handle_user_query(query: str) -> None:
    """Main handler: adds user msg, chooses answer (including small-talk), adds emoji."""
    if not query or st.session_state.processing:
        return

    normalized = query.strip()
    low = normalized.lower()

    st.session_state.processing = True
    append_message("user", normalized)

    # 1) Smart small-talk: thanks
    if any(w in low for w in ["thank", "thanks", "thanku", "thx"]):
        reply = "Aapka bahut bahut dhanyavaad! 😊 Agar aapko aur koi sawaal ho to please poochhiye."
        append_message("assistant", reply)
        st.session_state.processing = False
        return

    # 2) Smart small-talk: greetings / how-are-you (English + Hindi)
    if any(
        phrase in low
        for phrase in [
            "hello",
            "hi ",
            "hi!",
            "hey",
            "namaste",
            "namaskar",
            "kaise ho",
            "kese ho",
            "kaisi ho",
            "kya haal hai",
            "kya hal hai",
            "how are you",
            "how r u",
        ]
    ):
        profile = st.session_state.user_profile or {}
        name = profile.get("name", "student")
        reply = (
            f"Main bilkul theek hoon, dhanyavaad! 😊 Aap kaise ho {name}? "
            "Batao, main aapki kaise sahayta kar sakti hu?"
        )
        append_message("assistant", reply)
        st.session_state.processing = False
        return

    # 3) Normal flow via backend + personalization
    history = get_recent_history(HISTORY_TURNS)
    history_for_llm = history + [{"role": "user", "content": normalized}]

    with st.spinner("Searching..."):
        base_answer = call_backend_search(normalized)
        base_answer = personalize_answer(normalized, base_answer)

        # Robust detection of "no answer" from backend / VectorDB
        base_text = (base_answer or "").strip()
        lowered = base_text.lower()
        if (
            not base_text
            or "no matching answer" in lowered
            or "backend error" in lowered
            or "error contacting backend" in lowered
            or "could not connect" in lowered
            or lowered.startswith("❌")
        ):
            base_answer = "Sorry, I didn't understand."

        final_answer = call_llm_post_process(
            normalized, base_answer, history=history_for_llm
        )

    emoji = pick_emoji(normalized, final_answer)
    if emoji not in final_answer:
        final_answer = f"{final_answer} {emoji}"

    append_message("assistant", final_answer)
    log_chat_event(st.session_state.user_id, normalized, final_answer, ts=time.time())
    st.session_state.processing = False


def register_user(profile: dict):
    """Register/overwrite a user profile in the in-memory 'database'."""
    email_key = profile["email"].lower()
    st.session_state.registered_users[email_key] = profile


def register_sample_user(name: str, email: str, password: str):
    """Create/update the special sample user with attendance + CGPA."""
    profile = {
        "name": name or SAMPLE_USER["name"],
        "email": email,
        "password": password,
        "branch": SAMPLE_USER["branch"],
        "attendance": SAMPLE_USER["attendance"],
        "cgpa": SAMPLE_USER["cgpa"],
    }
    register_user(profile)
    st.session_state.user_id = profile["email"]
    st.session_state.user_profile = profile


# ---------------------- Sidebar: Login / Signup & controls ----------------------
with st.sidebar:
    st.title("🎓AcroBot : Apka Apna College Guide....!!")

    # Auth area
    if st.session_state.user_id:
        profile = st.session_state.user_profile or {}
        display_name = profile.get("name") or "Student"
        st.success(f"Logged in as: **{display_name}**")

        with st.expander("My details", expanded=True):
            st.markdown(f"**Name:** {profile.get('name', 'Not set')}")
            st.markdown(f"**Branch:** {profile.get('branch', 'Not set')}")
            if "attendance" in profile and "cgpa" in profile:
                st.markdown(f"**Attendance:** {profile['attendance']}")
                st.markdown(f"**Result (CGPA):** {profile['cgpa']}")

        if st.button("Log out"):
            st.session_state.user_id = None
            st.session_state.auth_mode = None
            st.session_state.user_profile = {}
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login"):
                st.session_state.auth_mode = "login"
        with col_b:
            if st.button("Sign up"):
                st.session_state.auth_mode = "signup"

        # Login form (email + password)
        if st.session_state.auth_mode == "login":
            st.markdown("**Login**")
            with st.form("login_form"):
                email = st.text_input("College email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    if email and password:
                        users = st.session_state.registered_users
                        profile = users.get(email.strip().lower())
                        if profile and password.strip() == profile.get("password"):
                            st.session_state.user_id = profile["email"]
                            st.session_state.user_profile = profile
                            st.success("Logged in successfully!")
                            st.session_state.auth_mode = None
                        else:
                            st.error(
                                "User not found or password incorrect. "
                                "Please check your details or sign up first."
                            )
                    else:
                        st.error("Please fill all fields.")

        # Signup form (name + email + password only)
        elif st.session_state.auth_mode == "signup":
            st.markdown("**Sign up**")
            with st.form("signup_form"):
                name = st.text_input("Full name")
                email = st.text_input("College email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create account")
                if submitted:
                    if name and email and password:
                        email_clean = email.strip()
                        pwd_clean = password.strip()
                        if email_clean.lower() == SAMPLE_USER["email"].lower():
                            # Special sample user: attach branch + attendance + cgpa
                            register_sample_user(name.strip(), email_clean, pwd_clean)
                        else:
                            profile = {
                                "name": name.strip(),
                                "email": email_clean,
                                "password": pwd_clean,
                            }
                            register_user(profile)
                            st.session_state.user_id = profile["email"]
                            st.session_state.user_profile = profile
                        st.success("Account created for this session! You are logged in.")
                        st.session_state.auth_mode = None
                    else:
                        st.error("Please fill name, email and password.")

    st.markdown("---")

    # View history option (sidebar)
    with st.expander("View chat history"):
        if not st.session_state.messages:
            st.caption("No messages yet.")
        else:
            for m in st.session_state.messages:
                who = "You" if m["role"] == "user" else "Bot"
                st.markdown(f"**{who}:** {m['content']}")

# ---------------------- Main layout ----------------------
top_col_left, top_col_right = st.columns([4, 2])

with top_col_left:
    st.markdown("### 🤖 Student FAQ Chatbot")
    st.markdown(
        """
        <span class="pill">24x7 help</span>
        <span class="pill">Campus info</span>
        <span class="pill">Transport</span>
        <span class="pill">Fees & Scholarships</span>
        """,
        unsafe_allow_html=True,
    )

    profile = st.session_state.user_profile or {}
    if st.session_state.user_id and profile.get("name"):
        username = profile["name"]
        st.write(
            f"Hello {username}, main aapki kaise sahayta kar sakti hu? "
            "(What can I help you with?)"
        )
    else:
        st.write(
            "Get instant answers about your campus: infrastructure, transport, fees, "
            "scholarships, placements, clubs and events."
        )

with top_col_right:
    st.image(
        "https://raw.githubusercontent.com/microsoft/fluentui-emoji/master/png/3d/student.png",
        width=120,
    )

st.markdown("")

# ---------------------- Chat area: history → suggestions → input ----------------------
with st.container():
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)

    # Placeholder container where history will be rendered.
    history_container = st.container()

    # 1. Suggestions
    st.markdown("**Try these example questions:**")
    cols = st.columns(3)
    followups = [
        "Where is the library?",
        "What is the annual fee structure for B.Tech IT?",
        "Are there any scholarships available for general category students?",
        "Which buses are available from 60 Feet Road?",
        "What student clubs are available?",
        "Show me upcoming campus drives.",
        "What is my attendance?",
        "Show me my result.",
    ]
    for i, q in enumerate(followups):
        if cols[i % 3].button(q, key=f"follow_{i}"):
            handle_user_query(q)

    # 2. Input bar at the bottom
    user_input = st.chat_input("Type your question here...")
    if user_input:
        handle_user_query(user_input)

    # 3. Render chat history (oldest at top, newest just above suggestions)
    with history_container:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                with st.chat_message(msg.get("role", "assistant")):
                    st.markdown(msg.get("content", ""))
            st.markdown("---")

    st.markdown("</div>", unsafe_allow_html=True)