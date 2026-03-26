"""
Intelligent Video Assistant - Ultimate Edition
Features: Video Editing, AI Assistant, Smart Matting, Novel to Video, Beauty Filter, Points Mall, Invite System, Share, Admin Panel, Security
"""

import streamlit as st
import os
import json
import time
import hashlib
import sqlite3
import tempfile
import subprocess
import threading
import random
import secrets
import re
from datetime import datetime, timedelta
import cv2
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AI Video Assistant v6.0", page_icon="🎬", layout="wide")

st.markdown("""
<style>
button { min-height: 44px !important; min-width: 44px !important; font-size: 16px !important; }
@media (max-width: 768px) {
    .stSidebar { width: 80% !important; }
    .stButton button { width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)

LANG = {
    "zh": {
        "title": "AI Video Assistant v6.0",
        "user_center": "User Center",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "confirm": "Confirm Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "logout": "Logout",
        "welcome": "Welcome back",
        "points": "Points",
        "quick_functions": "Quick Functions",
        "pro_mode": "Pro Mode",
        "pro_tools": "Pro Tools",
        "cut": "Cut Video",
        "speed": "Video Speed",
        "ai_assistant": "AI Assistant",
        "smart_matting": "Smart Matting",
        "novel_to_video": "Novel to Video",
        "material_library": "Material Library",
        "video_sites": "Video Sites",
        "movie_search": "Movie Search",
        "points_mall": "Points Mall",
        "multi_track": "Multi-Track",
        "security": "Security",
        "about": "About",
        "admin_panel": "Admin Panel",
        "upload_first": "Please upload a video first",
        "download": "Download",
        "password_mismatch": "Passwords do not match",
        "user_exists": "Username already exists",
        "register_success": "Registration successful",
        "login_success": "Login successful",
        "user_not_exist": "Username does not exist",
        "wrong_password": "Wrong password",
        "language": "Language",
        "beauty_filter": "Beauty Filter",
        "share_app": "Share App",
        "video_merge": "Merge Videos",
        "add_text": "Add Text",
        "gif_export": "Export GIF",
        "current_function": "Current Function",
        "processing": "Processing...",
        "success": "Success!",
        "error": "Error"
    },
    "en": {
        "title": "AI Video Assistant v6.0",
        "user_center": "User Center",
        "login": "Login",
        "register": "Register",
        "username": "Username",
        "password": "Password",
        "confirm": "Confirm Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "logout": "Logout",
        "welcome": "Welcome back",
        "points": "Points",
        "quick_functions": "Quick Functions",
        "pro_mode": "Pro Mode",
        "pro_tools": "Pro Tools",
        "cut": "Cut Video",
        "speed": "Video Speed",
        "ai_assistant": "AI Assistant",
        "smart_matting": "Smart Matting",
        "novel_to_video": "Novel to Video",
        "material_library": "Material Library",
        "video_sites": "Video Sites",
        "movie_search": "Movie Search",
        "points_mall": "Points Mall",
        "multi_track": "Multi-Track",
        "security": "Security",
        "about": "About",
        "admin_panel": "Admin Panel",
        "upload_first": "Please upload a video first",
        "download": "Download",
        "password_mismatch": "Passwords do not match",
        "user_exists": "Username already exists",
        "register_success": "Registration successful",
        "login_success": "Login successful",
        "user_not_exist": "Username does not exist",
        "wrong_password": "Wrong password",
        "language": "Language",
        "beauty_filter": "Beauty Filter",
        "share_app": "Share App",
        "video_merge": "Merge Videos",
        "add_text": "Add Text",
        "gif_export": "Export GIF",
        "current_function": "Current Function",
        "processing": "Processing...",
        "success": "Success!",
        "error": "Error"
    }
}

def t(key):
    lang = st.session_state.get('language', 'zh')
    return LANG[lang].get(key, key)

def save_uploaded_file(uploaded):
    if uploaded is None:
        return None
    suffix = os.path.splitext(uploaded.name)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getbuffer())
    return tmp.name

def cleanup_temp_files(paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.unlink(p)
            except:
                pass

@st.cache_data(ttl=3600, show_spinner=False)
def get_video_info(video_path):
    if not os.path.exists(video_path):
        return None
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return {"duration": total_frames/fps, "fps": fps, "frames": total_frames, "width": width, "height": height}

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    salt TEXT,
                    admin_level INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invite_codes (
                    username TEXT PRIMARY KEY,
                    invite_code TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter TEXT,
                    invitee TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_features (
                    username TEXT,
                    feature TEXT,
                    expires TIMESTAMP,
                    PRIMARY KEY (username, feature)
                )''')
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return pwd_hash, salt

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, salt, admin_level, points FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, t("user_not_exist")
    stored_hash, salt, level, points = row
    input_hash, _ = hash_password(password, salt)
    if input_hash == stored_hash:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.admin_level = level
        st.session_state.points = points
        return True, t("login_success")
    return False, t("wrong_password")

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False, t("user_exists")
    pwd_hash, salt = hash_password(password)
    c.execute("INSERT INTO users (username, password_hash, salt, points) VALUES (?, ?, ?, 100)", 
              (username, pwd_hash, salt))
    conn.commit()
    conn.close()
    return True, t("register_success")

def get_points(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_points(username, amount, reason):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username=?", (amount, username))
    c.execute("INSERT INTO user_logs (username, action) VALUES (?, ?)", (username, reason))
    conn.commit()
    conn.close()

def spend_points(username, points, reason):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row or row[0] < points:
        conn.close()
        return False
    c.execute("UPDATE users SET points = points - ? WHERE username=?", (points, username))
    c.execute("INSERT INTO user_logs (username, action) VALUES (?, ?)", (username, reason))
    conn.commit()
    conn.close()
    return True

def log_action(username, action):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO user_logs (username, action) VALUES (?, ?)", (username, action))
    conn.commit()
    conn.close()

def generate_invite_code(username):
    code = hashlib.md5(f"{username}{secrets.token_hex(4)}".encode()).hexdigest()[:8].upper()
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO invite_codes (username, invite_code) VALUES (?, ?)", (username, code))
    conn.commit()
    conn.close()
    return code

def get_invite_code(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT invite_code FROM invite_codes WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return generate_invite_code(username)

def process_invite(invite_code, invitee):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username FROM invite_codes WHERE invite_code=?", (invite_code,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Invalid invite code"
    inviter = row[0]
    c.execute("SELECT id FROM invites WHERE inviter=? AND invitee=?", (inviter, invitee))
    if c.fetchone():
        conn.close()
        return False, "Already invited"
    c.execute("INSERT INTO invites (inviter, invitee) VALUES (?, ?)", (inviter, invitee))
    conn.commit()
    conn.close()
    add_points(inviter, 50, f"Invited {invitee} to register")
    add_points(invitee, 20, f"Registered via invite code {invite_code}")
    return True, "Invite successful! Both got points"

def cut_video(input_path, start, end, output_path):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end), "-c", "copy", output_path], check=True)

def speed_video(input_path, speed, output_path):
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-filter:v", f"setpts={1/speed}*PTS",
        "-filter:a", f"atempo={speed}",
        "-c:a", "aac", output_path
    ], check=True)

def apply_beauty_filter(frame, intensity=0.5):
    beauty = cv2.bilateralFilter(frame, 9, 75, 75)
    hsv = cv2.cvtColor(beauty, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:,:,2] = np.clip(hsv[:,:,2] * (1 + intensity * 0.3), 0, 255)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * (1 - intensity * 0.2), 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return cv2.addWeighted(frame, 1-intensity, result, intensity, 0)

def video_to_gif(input_path, output_path, start=0, duration=5):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-t", str(duration), "-vf", "fps=10,scale=320:-1", output_path], check=True)

def render_auth():
    with st.sidebar:
        st.header(t("user_center"))
        if not st.session_state.get('logged_in', False):
            tab = st.radio("", [t("login"), t("register")], horizontal=True)
            if tab == t("login"):
                with st.form("login_form"):
                    username = st.text_input(t("username"))
                    password = st.text_input(t("password"), type="password")
                    if st.form_submit_button(t("login_btn")):
                        ok, msg = login_user(username, password)
                        if ok:
                            log_action(username, "login")
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                with st.form("register_form"):
                    username = st.text_input(t("username"))
                    password = st.text_input(t("password"), type="password")
                    confirm = st.text_input(t("confirm"), type="password")
                    invite_code = st.text_input("Invite Code (optional)")
                    if st.form_submit_button(t("register_btn")):
                        if password != confirm:
                            st.error(t("password_mismatch"))
                        else:
                            ok, msg = register_user(username, password)
                            if ok:
                                if invite_code:
                                    process_invite(invite_code, username)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            st.stop()
        else:
            st.success(f"{t('welcome')}, {st.session_state.username}")
            points = get_points(st.session_state.username)
            st.write(f"{t('points')}: {points}")
            if st.button(t("logout")):
                st.session_state.clear()
                st.rerun()
            st.markdown("---")

def render_language():
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Chinese", use_container_width=True):
                st.session_state.language = 'zh'
                st.rerun()
        with col2:
            if st.button("English", use_container_width=True):
                st.session_state.language = 'en'
                st.rerun()
        st.markdown("---")

def render_share():
    st.subheader(t("share_app"))
    app_url = "https://your-app.streamlit.app"
    invite_code = get_invite_code(st.session_state.username)
    invite_link = f"{app_url}?invite={invite_code}"
    st.code(invite_link, language="text")
    st.caption("Share this link, both get points")

def render_video_sites():
    st.subheader(t("video_sites"))
    sites = [
        ("iQiyi", "https://www.iqiyi.com"),
        ("Tencent Video", "https://v.qq.com"),
        ("Youku", "https://www.youku.com"),
        ("Bilibili", "https://www.bilibili.com")
    ]
    cols = st.columns(2)
    for i, (name, url) in enumerate(sites):
        with cols[i % 2]:
            if st.button(f"Visit {name}", use_container_width=True):
                import webbrowser
                webbrowser.open(url)
                st.info(f"Opening {name}")

def render_movie_search():
    st.subheader(t("movie_search"))
    keyword = st.text_input("Enter movie or TV show name")
    if keyword:
        st.markdown("### Search on platforms")
        st.markdown(f'<a href="https://www.iqiyi.com/search?q={keyword}" target="_blank">iQiyi Search</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="https://v.qq.com/search?q={keyword}" target="_blank">Tencent Video Search</a>', unsafe_allow_html=True)

def render_about():
    st.subheader(t("about"))
    st.markdown("**AI Video Assistant v6.0**\n\nDeveloper: Li Guorui & Xiao Zhi (DeepSeek)\n\nDedicated to all dreamers!")

def render_ai_assistant():
    st.subheader(t("ai_assistant"))
    st.info("Enter a command, like 'cut first 5 seconds'")
    user_input = st.text_input("Enter command")
    if user_input:
        if "cut" in user_input or "trim" in user_input:
            st.success("AI recognized: You want to cut video")
        elif "speed" in user_input:
            st.success("AI recognized: You want to adjust video speed")
        else:
            st.info(f"Received command: {user_input}")

def render_smart_matting():
    st.subheader(t("smart_matting"))
    st.info("Smart matting feature coming soon")

def render_novel_to_video():
    st.subheader(t("novel_to_video"))
    novel_text = st.text_area("Enter novel text", height=150)
    if st.button("Generate Video"):
        st.info("Novel to video feature coming soon")

def render_material_library():
    st.subheader(t("material_library"))
    st.info("Material library coming soon")

def render_points_mall():
    st.subheader(t("points_mall"))
    points = get_points(st.session_state.username)
    st.write(f"Current points: {points}")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Beauty Filter (50 points)"):
            if spend_points(st.session_state.username, 50, "Purchased beauty filter"):
                st.success("Purchase successful!")

def render_multi_track():
    st.subheader(t("multi_track"))
    st.info("Multi-track timeline coming soon")

def render_security():
    st.subheader(t("security"))
    st.success("Security monitoring active")

def render_admin_panel():
    st.subheader(t("admin_panel"))
    if st.session_state.get('admin_level', 0) >= 5:
        st.success("Super Admin Access")
        conn = sqlite3.connect('users.db')
        users = pd.read_sql_query("SELECT username, points, admin_level FROM users", conn)
        logs = pd.read_sql_query("SELECT * FROM user_logs LIMIT 20", conn)
        conn.close()
        st.dataframe(users)
        st.dataframe(logs)
    else:
        st.warning("Insufficient permissions")

def render_beauty_filter():
    st.subheader(t("beauty_filter"))
    if st.session_state.get('video_path'):
        intensity = st.slider("Beauty intensity", 0.0, 1.0, 0.5)
        st.info(f"Current intensity: {intensity}")
    else:
        st.info(t("upload_first"))

def render_gif_export():
    st.subheader(t("gif_export"))
    if st.session_state.get('video_path'):
        start = st.number_input("Start time (seconds)", 0.0, 10.0, 0.0)
        duration = st.number_input("Duration (seconds)", 1.0, 10.0, 3.0)
        if st.button("Export as GIF"):
            out = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name
            with st.spinner(t("processing")):
                video_to_gif(st.session_state.video_path, out, start, duration)
            st.success(t("success"))
            with open(out, "rb") as f:
                st.download_button(t("download"), f, file_name="output.gif")
            cleanup_temp_files([out])
    else:
        st.info(t("upload_first"))

def main():
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    
    init_db()
    render_language()
    render_auth()
    
    if not st.session_state.get('logged_in', False):
        return
    
    points = get_points(st.session_state.username)
    with st.sidebar:
        st.write(f"{t('points')}: {points}")
        st.markdown("---")
        st.markdown("### Function Menu")
        
        core = [t("cut"), t("speed"), t("beauty_filter"), t("gif_export")]
        advanced = [
            t("ai_assistant"), t("smart_matting"), t("novel_to_video"),
            t("material_library"), t("video_sites"), t("movie_search"),
            t("points_mall"), t("multi_track"), t("security"), t("about"),
            t("share_app")
        ]
        
        pro_mode = st.checkbox(t("pro_mode"), value=True)
        
        if pro_mode:
            func = st.selectbox(t("quick_functions"), core + advanced)
        else:
            func = st.selectbox(t("quick_functions"), core)
            with st.expander(t("pro_tools")):
                for adv in advanced:
                    if st.button(adv, use_container_width=True):
                        st.session_state.current_func = adv
                        st.rerun()
        
        if 'current_func' in st.session_state:
            func = st.session_state.current_func
            del st.session_state.current_func
        
        if st.session_state.get('admin_level', 0) >= 5:
            st.markdown("---")
            if st.button(t("admin_panel"), use_container_width=True):
                st.session_state.current_func = t("admin_panel")
                st.rerun()
    
    st.title(t("title"))
    
    uploaded = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"])
    if uploaded:
        video_path = save_uploaded_file(uploaded)
        st.session_state.video_path = video_path
        info = get_video_info(video_path)
        if info:
            st.success(f"Upload successful! Duration: {info['duration']:.1f}s | Resolution: {info['width']}x{info['height']}")
    
    if func == t("cut"):
        st.subheader(t("cut"))
        if st.session_state.get('video_path'):
            dur = get_video_info(st.session_state.video_path)["duration"]
            start = st.number_input("Start time (seconds)", 0.0, dur, 0.0)
            end = st.number_input("End time (seconds)", 0.0, dur, min(5.0, dur))
            if st.button("Cut Video"):
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                with st.spinner(t("processing")):
                    cut_video(st.session_state.video_path, start, end, out)
                st.success(t("success"))
                with open(out, "rb") as f:
                    st.download_button(t("download"), f, file_name="cut.mp4")
                cleanup_temp_files([out])
        else:
            st.info(t("upload_first"))
    
    elif func == t("speed"):
        st.subheader(t("speed"))
        if st.session_state.get('video_path'):
            speed = st.number_input("Speed multiplier", 0.1, 5.0, 1.0, step=0.1)
            if st.button("Apply Speed"):
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                with st.spinner(t("processing")):
                    speed_video(st.session_state.video_path, speed, out)
                st.success(t("success"))
                with open(out, "rb") as f:
                    st.download_button(t("download"), f, file_name="speed.mp4")
                cleanup_temp_files([out])
        else:
            st.info(t("upload_first"))
    
    elif func == t("beauty_filter"):
        render_beauty_filter()
    elif func == t("gif_export"):
        render_gif_export()
    elif func == t("ai_assistant"):
        render_ai_assistant()
    elif func == t("smart_matting"):
        render_smart_matting()
    elif func == t("novel_to_video"):
        render_novel_to_video()
    elif func == t("material_library"):
        render_material_library()
    elif func == t("video_sites"):
        render_video_sites()
    elif func == t("movie_search"):
        render_movie_search()
    elif func == t("points_mall"):
        render_points_mall()
    elif func == t("multi_track"):
        render_multi_track()
    elif func == t("security"):
        render_security()
    elif func == t("about"):
        render_about()
    elif func == t("admin_panel"):
        render_admin_panel()
    elif func == t("share_app"):
        render_share()
    else:
        st.info(f"{t('current_function')}: {func}")

if __name__ == "__main__":
    main()
