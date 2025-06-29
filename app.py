# app.py
import streamlit as st
import re
import os
from datetime import datetime
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
import firebase_admin
from deep_translator import GoogleTranslator
from gemini import init_gemini, generate_palace_scene
from firebase_helper import init_firebase
from streamlit_lottie import st_lottie
from lottie_helper import get_lottie_animation

# --- Utilities ---
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def translate_text(text, target_lang='hi'):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        return f"\u274c Translation failed: {e}"

# --- Init Firebase & Gemini ---
firebase = init_firebase()
auth = firebase.auth()
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
init_gemini(GEMINI_API_KEY)

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase_admin"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- UI Setup ---
st.set_page_config(page_title="Memory Palace Builder", layout="centered")

st.markdown("""
    <style>
    /* Base font & spacing */
    html, body {
        font-size: 16px;
        line-height: 1.6;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Streamlit containers */
    .block-container {
        padding: 1rem 1rem 3rem;
        max-width: 100% !important;
    }

    /* Mobile responsive */
    @media only screen and (max-width: 600px) {
        .block-container {
            padding: 0.5rem;
        }

        h1, h2, h3 {
            font-size: 1.2em !important;
        }

        .stButton>button {
            font-size: 0.9em;
            padding: 0.4em 1em;
        }

        .stTextInput>div>div>input,
        .stSelectbox>div>div>div {
            font-size: 1em !important;
        }

        img {
            max-width: 100% !important;
            height: auto !important;
        }
    }

    /* Back to top link spacing */
    a[href="#top"] {
        display: block;
        margin-top: 1rem;
        text-align: right;
        font-size: 0.9rem;
        color: #888;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)


st.title("\U0001F9E0 Memory Palace Builder")

# --- Sidebar ---
if "user" not in st.session_state:
    st.sidebar.markdown("## Menu")
    menu = st.sidebar.radio("Choose an option", ["Login", "Sign Up"], key="main_menu")
else:
    user = st.session_state["user"]
    user_id = user.get("localId", "")
    display_name = user.get("name") or user.get("username") or user.get("email", "").split("@")[0]

    st.sidebar.markdown("## Mine")
    if user.get("avatar"):
        st.sidebar.image(user["avatar"], width=36)
    st.sidebar.markdown(f"👋 Hello, **{display_name}**")

    # Language preference
    language_map = {
        "English": "en", "Hindi": "hi", "Tamil": "ta", "Telugu": "te", "Kannada": "kn",
        "Bengali": "bn", "Marathi": "mr", "Gujarati": "gu", "Malayalam": "ml", "Punjabi": "pa"
    }
    selected_lang = st.sidebar.selectbox("🌐 Preferred Language", list(language_map.keys()), key="lang_select")
    st.session_state["user_language"] = selected_lang
    st.session_state["lang_code"] = language_map[selected_lang]

    # Menu options after login
    menu = st.sidebar.radio("Navigate", ["Generate", "My Palaces", "Profile"], key="mine_menu")

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        del st.session_state["user"]
        st.rerun()

# --- Profile Section ---
def show_user_profile():
    st.subheader("\U0001F464 My Profile")
    user_info = st.session_state.get("user", {})
    user_id = user_info.get("localId")
    user_doc = db.collection("users").document(user_id).get()
    data = user_doc.to_dict() if user_doc.exists else {}

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if not st.session_state.edit_mode:
        st.image(data.get("avatar", ""), width=100)
        st.markdown(f"**Name:** {data.get('name', '')}")
        st.markdown(f"**Username:** @{data.get('username', '')}")
        st.markdown(f"**Email:** {user_info.get('email', '')}")
        st.markdown(f"**Profession:** {data.get('profession', '')}")
        st.markdown(f"**About Me:**\n\n{data.get('bio', '')}")
        if st.button("✏️ Edit Profile"):
            st.session_state.edit_mode = True
    else:
        name = st.text_input("Name", data.get("name", ""))
        username = st.text_input("Username", data.get("username", ""))
        profession = st.selectbox("Profession", ["Student", "Professional", "Other"],
                                  index=["Student", "Professional", "Other"].index(data.get("profession", "Student")))
        bio = st.text_area("About Me", data.get("bio", ""))
        avatar_options = {
            "🦁 Lion": "https://api.dicebear.com/7.x/adventurer/svg?seed=Lion",
            "🐯 Tiger": "https://api.dicebear.com/7.x/adventurer/svg?seed=Tiger",
            "🐉 Dragon": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dragon",
            "🐵 Monkey": "https://api.dicebear.com/7.x/adventurer/svg?seed=Monkey",
            "🔥 Phoenix": "https://api.dicebear.com/7.x/adventurer/svg?seed=Phoenix",
            "🐺 Wolf": "https://api.dicebear.com/7.x/adventurer/svg?seed=Wolf",
            "🐻 Bear": "https://api.dicebear.com/7.x/adventurer/svg?seed=Bear",
            "🐱 Cat": "https://api.dicebear.com/7.x/adventurer/svg?seed=Cat",
            "🐶 Dog": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dog",
            "🦊 Fox": "https://api.dicebear.com/7.x/adventurer/svg?seed=Fox"
        }
        avatar_name = st.selectbox("Avatar", list(avatar_options.keys()))
        avatar_url = avatar_options[avatar_name]
        st.image(avatar_url, width=100)

        if st.button("💾 Save Profile"):
            updated = {"name": name, "username": username, "profession": profession, "bio": bio, "avatar": avatar_url}
            db.collection("users").document(user_id).set(updated, merge=True)
            st.session_state.user.update(updated)
            st.success("✅ Profile updated!")
            st.session_state.edit_mode = False
            st.experimental_rerun()

# --- Main Logic ---
if menu == "Login":
    st.subheader("🔐 Login")
    
    # Avoid empty label warning
    email = st.text_input("📧 Email", key="login_email").strip()
    password = st.text_input("🔒 Password", type="password", key="login_password")

    if st.button("Log In"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format")
        else:
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                user_id = user["localId"]

                user_doc = db.collection("users").document(user_id).get()
                if user_doc.exists:
                    user.update(user_doc.to_dict())

                # Save user info to session
                st.session_state["user"] = user
                st.success("✅ Logged in successfully!")

                st.rerun()  # Ensures the app reruns with user in state

            except Exception as e:
                st.error("❌ Login failed: Invalid email or password")
                # st.warning(str(e))  # Uncomment for debugging

elif menu == "Sign Up":
    st.subheader("📝 Sign Up")
    name = st.text_input("Full Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    profession = st.selectbox("Profession", ["Student", "Professional", "Other"])
    avatar_options = {
        "🦁 Lion": "https://api.dicebear.com/7.x/adventurer/svg?seed=Lion",
        "🐯 Tiger": "https://api.dicebear.com/7.x/adventurer/svg?seed=Tiger",
        "🐵 Monkey": "https://api.dicebear.com/7.x/adventurer/svg?seed=Monkey",
        "🐉 Dragon": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dragon",
        "🔥 Phoenix": "https://api.dicebear.com/7.x/adventurer/svg?seed=Phoenix",
        "🐺 Wolf": "https://api.dicebear.com/7.x/adventurer/svg?seed=Wolf",
        "🐻 Bear": "https://api.dicebear.com/7.x/adventurer/svg?seed=Bear",
        "🐱 Cat": "https://api.dicebear.com/7.x/adventurer/svg?seed=Cat",
        "🐶 Dog": "https://api.dicebear.com/7.x/adventurer/svg?seed=Dog",
        "🦊 Fox": "https://api.dicebear.com/7.x/adventurer/svg?seed=Fox"
    }
    avatar_name = st.selectbox("Avatar", list(avatar_options.keys()))
    avatar_url = avatar_options[avatar_name]
    st.image(avatar_url, width=100)

    if st.button("Sign Up"):
        if not is_valid_email(email) or not name or not username:
            st.error("❌ All fields required")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                user_id = user["localId"]
                db.collection("users").document(user_id).set({
                    "email": email, "username": username, "name": name,
                    "profession": profession, "avatar": avatar_url, "bio": ""
                })
                user.update({"username": username, "name": name, "avatar": avatar_url})
                st.session_state["user"] = user
                st.success("✅ Account created")
                st.experimental_rerun()
            except Exception:
                st.error("❌ Sign up failed")

elif menu == "Generate" and "user" in st.session_state:
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("🔮 Generate Memory Palace")
        topic = st.text_input("📌 Enter a topic to remember", key="topic_input")

        locations = [
            "🏠 My Home",
            "🏫 My School",
            "🎮 Game World",
            "📚 Library",
            "✍️ Other (let me type)"
        ]

        choice = st.selectbox("📍 Choose a memory palace location", locations, key="location_choice")
        location = st.text_input("📝 Describe your own place", key="custom_location") if choice == "✍️ Other (let me type)" else choice

    with col2:
        from streamlit_lottie import st_lottie
        from lottie_helper import get_lottie_animation
        st_lottie(get_lottie_animation("brain"), height=120, key="brain_small")

    if st.button("🚀 Generate Palace"):
        if not topic or not location:
            st.warning("⚠️ Please enter both a topic and a location.")
        else:
            prompt = (
                f"Imagine a vivid, surreal, and fun scene where the concept of '{topic}' is memorably placed inside "
                f"'{location}' as part of a memory palace. Do not be logical — be imaginative and symbolic."
            )

            with st.spinner("Generating memory palace... Please wait (up to 30 seconds)..."):
                try:
                    scene = generate_palace_scene(prompt)
                    st.success("✅ Memory Palace Generated")
                    st.markdown("### 🧠 English")
                    st.write(scene)

                    # Optional translation
                    lang_code = st.session_state.get("lang_code", "en")
                    user_lang = st.session_state.get("user_language", "English")
                    translated_scene = ""

                    if lang_code != "en":
                        translated_scene = translate_text(scene, lang_code)
                        st.markdown(f"### 🌐 Translated ({user_lang})")
                        st.write(translated_scene)

                    # Save to Firestore
                    db.collection("users").document(
                        st.session_state["user"]["localId"]
                    ).collection("palaces").add({
                        "topic": topic,
                        "scene": scene,
                        "translated_scene": translated_scene,
                        "location": location,
                        "created_at": datetime.utcnow()
                    })

                    st.success("📂 Palace saved to your collection!")

                except Exception as e:
                    st.error("❌ Reached Today Limit or the request timed out.")
                    st.exception(e)  # Optional: helpful for debugging

elif menu == "My Palaces" and "user" in st.session_state:
    st.subheader("📚 My Palaces")
    st.markdown("<a name='top'></a>", unsafe_allow_html=True)
    user_id = st.session_state["user"]["localId"]
    docs = db.collection("users").document(user_id).collection("palaces").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    docs = list(docs)
    st.markdown(f"### Total: {len(docs)}")
    for doc in docs:
        data = doc.to_dict()
        st.markdown(f"### \U0001F3DB️ {data.get('topic')} — *{data.get('location')}*")
        st.markdown(f"🧠 **Scene :**\n\n{data.get('scene')}")
        if data.get("translated_scene"):
            lang_name = st.session_state.get("user_language", "Translated")
            st.markdown(f"🌐 **Translation :**\n\n{data.get('translated_scene')}")
        st.markdown("[⬆️ Back to top](#top)", unsafe_allow_html=True)
        st.markdown("---")

elif menu == "Profile" and "user" in st.session_state:
    show_user_profile()
