"""
小智 - 智能视频助手 v6.0
包含：视频剪辑、小智AI、版图系统
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

st.set_page_config(page_title="小智 - 智能视频助手", page_icon="🤖", layout="wide")

# ========== CSS样式 ==========
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.main-header h1 {
    color: white;
    font-size: 3rem;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}
.main-header p {
    color: rgba(255,255,255,0.9);
    font-size: 1.2rem;
}
.card {
    background: white;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 0.6rem 1.5rem;
    font-weight: bold;
    transition: all 0.3s ease;
}
.stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 5px 20px rgba(102,126,234,0.4);
}
.points-badge {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 5px 15px;
    border-radius: 50px;
    display: inline-block;
    font-weight: bold;
}
.xiaozhi-avatar {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    margin: 0 auto 15px auto;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-5px); }
    100% { transform: translateY(0px); }
}
.sidebar-header {
    text-align: center;
    padding: 10px 0;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.2);
}
.xiaozhi-badge {
    background: linear-gradient(135deg, #667eea, #764ba2);
    padding: 5px 15px;
    border-radius: 25px;
    display: inline-block;
    color: white;
    font-weight: bold;
    font-size: 14px;
}
@media (max-width: 768px) {
    .main-header h1 {
        font-size: 1.8rem;
    }
    .stButton button {
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)

# ========== 语言资源 ==========
LANG = {
    "zh": {
        "title": "小智 - 智能视频助手",
        "subtitle": "你的AI视频创作伙伴",
        "user_center": "用户中心",
        "login": "登录",
        "register": "注册",
        "username": "用户名",
        "password": "密码",
        "confirm": "确认密码",
        "login_btn": "登录",
        "register_btn": "注册",
        "logout": "退出登录",
        "welcome": "欢迎回来",
        "points": "积分",
        "quick_functions": "快速功能",
        "pro_mode": "专业模式",
        "pro_tools": "专业工具",
        "cut": "✂️ 剪切视频",
        "speed": "⚡ 视频变速",
        "ai_assistant": "🤖 小智AI助手",
        "beauty_filter": "✨ 美颜滤镜",
        "gif_export": "🎞️ 导出GIF",
        "poster_system": "🎨 版图系统",
        "upload_first": "请先上传视频",
        "download": "下载视频",
        "password_mismatch": "两次密码不一致",
        "user_exists": "用户名已存在",
        "register_success": "注册成功",
        "login_success": "登录成功",
        "user_not_exist": "用户名不存在",
        "wrong_password": "密码错误",
        "language": "语言",
        "chinese": "中文",
        "english": "English",
        "processing": "处理中...",
        "success": "处理成功！",
        "error": "处理失败"
    },
    "en": {
        "title": "XiaoZhi - AI Video Assistant",
        "subtitle": "Your AI Video Creation Partner",
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
        "cut": "✂️ Cut Video",
        "speed": "⚡ Video Speed",
        "ai_assistant": "🤖 XiaoZhi AI",
        "beauty_filter": "✨ Beauty Filter",
        "gif_export": "🎞️ Export GIF",
        "poster_system": "🎨 Poster System",
        "upload_first": "Please upload a video first",
        "download": "Download",
        "password_mismatch": "Passwords do not match",
        "user_exists": "Username already exists",
        "register_success": "Registration successful",
        "login_success": "Login successful",
        "user_not_exist": "Username does not exist",
        "wrong_password": "Wrong password",
        "language": "Language",
        "chinese": "中文",
        "english": "English",
        "processing": "Processing...",
        "success": "Success!",
        "error": "Error"
    }
}

def t(key):
    lang = st.session_state.get('language', 'zh')
    return LANG[lang].get(key, key)

# ========== 辅助函数 ==========
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

# ========== 数据库 ==========
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
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    admin_level = 5 if count == 0 else 0
    c.execute("INSERT INTO users (username, password_hash, salt, points, admin_level) VALUES (?, ?, ?, 100, ?)", 
              (username, pwd_hash, salt, admin_level))
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

# ========== 视频处理 ==========
def cut_video(input_path, start, end, output_path):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end), "-c", "copy", output_path], check=True)

def speed_video(input_path, speed, output_path):
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-filter:v", f"setpts={1/speed}*PTS",
        "-filter:a", f"atempo={speed}",
        "-c:a", "aac", output_path
    ], check=True)

def video_to_gif(input_path, output_path, start=0, duration=5):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-t", str(duration), "-vf", "fps=10,scale=320:-1", output_path], check=True)

# ========== 版图系统 ==========
import os as poster_os
import cv2 as poster_cv2
import sqlite3 as poster_sqlite3

POSTER_IMAGE_DIR = "poster_images"
poster_os.makedirs(POSTER_IMAGE_DIR, exist_ok=True)

def init_poster_tables():
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator TEXT,
        title TEXT,
        description TEXT,
        price_points INTEGER DEFAULT 100,
        rarity TEXT DEFAULT '普通',
        status TEXT DEFAULT 'on_sale',
        likes INTEGER DEFAULT 0,
        buys INTEGER DEFAULT 0,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS poster_collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        poster_id INTEGER,
        bought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS poster_earnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator TEXT,
        poster_id INTEGER,
        buyer TEXT,
        amount_points INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def compress_and_save_image(frame, poster_id):
    height, width = frame.shape[:2]
    max_size = 300
    if width > max_size:
        ratio = max_size / width
        new_width = max_size
        new_height = int(height * ratio)
        frame = poster_cv2.resize(frame, (new_width, new_height))
    filepath = poster_os.path.join(POSTER_IMAGE_DIR, f"{poster_id}.jpg")
    poster_cv2.imwrite(filepath, frame, [poster_cv2.IMWRITE_JPEG_QUALITY, 60])
    return filepath

def extract_frame_from_video(video_path, poster_id):
    cap = poster_cv2.VideoCapture(video_path)
    total_frames = int(cap.get(poster_cv2.CAP_PROP_FRAME_COUNT))
    middle_frame = total_frames // 2
    cap.set(poster_cv2.CAP_PROP_POS_FRAMES, middle_frame)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return compress_and_save_image(frame, poster_id)
    return None

def render_poster_generator():
    st.markdown("### 🎨 生成版图")
    if not st.session_state.get('video_path'):
        st.info("请先上传视频")
        return
    video_path = st.session_state.video_path
    info = get_video_info(video_path)
    if info:
        st.video(video_path)
        st.caption(f"时长：{info['duration']:.1f}秒 | {info['width']}x{info['height']}")
    with st.form("poster_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("版图标题")
        with col2:
            price = st.number_input("价格（积分）", min_value=10, max_value=10000, value=100, step=10)
        rarity = st.selectbox("稀有度", ["普通", "稀有", "史诗", "传说"])
        description = st.text_area("版图描述", height=60)
        if st.form_submit_button("✨ 生成版图", use_container_width=True):
            if not title:
                st.warning("请输入标题")
                return
            with st.spinner("生成中..."):
                conn = poster_sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("INSERT INTO posters (creator, title, description, price_points, rarity) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state.username, title, description, price, rarity))
                poster_id = c.lastrowid
                conn.commit()
                image_path = extract_frame_from_video(video_path, poster_id)
                if image_path:
                    c.execute("UPDATE posters SET image_path = ? WHERE id = ?", (image_path, poster_id))
                    conn.commit()
                    st.success(f"✅ 版图「{title}」生成成功！")
                    st.info(f"💰 {price}积分 | 🏷️ {rarity}")
                    st.balloons()
                else:
                    st.error("提取失败")
                conn.close()

def render_poster_mall():
    st.markdown("### 🛒 版图商城")
    if 'poster_page' not in st.session_state:
        st.session_state.poster_page = 1
    page_size = 12
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters WHERE status = 'on_sale'")
    total = c.fetchone()[0]
    total_pages = (total + page_size - 1) // page_size
    offset = (st.session_state.poster_page - 1) * page_size
    c.execute("SELECT id, creator, title, price_points, rarity, likes, buys, image_path FROM posters WHERE status = 'on_sale' ORDER BY created_at DESC LIMIT ? OFFSET ?", (page_size, offset))
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("暂无版图")
        return
    cols = st.columns(4)
    for i, poster in enumerate(posters):
        poster_id, creator, title, price, rarity, likes, buys, image_path = poster
        with cols[i % 4]:
            if image_path and poster_os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            else:
                st.markdown('<div style="height:150px; background:#f0f0f0; border-radius:10px;"></div>', unsafe_allow_html=True)
            st.markdown(f"**{title[:20]}**")
            st.caption(f"👤 {creator}")
            st.caption(f"💰 {price}积分 | 🏷️ {rarity}")
            st.caption(f"❤️ {likes} | 🛒 {buys}")
            if st.button(f"购买", key=f"buy_{poster_id}"):
                if spend_points(st.session_state.username, price, f"购买版图{title}"):
                    conn2 = poster_sqlite3.connect('users.db')
                    c2 = conn2.cursor()
                    c2.execute("INSERT INTO poster_collections (user, poster_id) VALUES (?, ?)", (st.session_state.username, poster_id))
                    c2.execute("UPDATE posters SET buys = buys + 1 WHERE id = ?", (poster_id,))
                    c2.execute("INSERT INTO poster_earnings (creator, poster_id, buyer, amount_points) VALUES (?, ?, ?, ?)",
                               (creator, poster_id, st.session_state.username, price))
                    conn2.commit()
                    conn2.close()
                    creator_points = int(price * 0.8)
                    add_points(creator, creator_points, f"版图{title}被购买")
                    st.success(f"购买成功！{creator}获得{creator_points}积分")
                    st.rerun()
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            col_prev, col_page, col_next = st.columns(3)
            if st.session_state.poster_page > 1:
                if col_prev.button("◀"):
                    st.session_state.poster_page -= 1
                    st.rerun()
            col_page.markdown(f"<div style='text-align:center'>{st.session_state.poster_page}/{total_pages}</div>", unsafe_allow_html=True)
            if st.session_state.poster_page < total_pages:
                if col_next.button("▶"):
                    st.session_state.poster_page += 1
                    st.rerun()

def render_my_posters():
    st.markdown("### 🖼️ 我的版图")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, price_points, rarity, likes, buys, image_path, status FROM posters WHERE creator = ? ORDER BY created_at DESC", (st.session_state.username,))
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("还没有版图")
        return
    cols = st.columns(3)
    for i, poster in enumerate(posters):
        poster_id, title, price, rarity, likes, buys, image_path, status = poster
        with cols[i % 3]:
            if image_path and poster_os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            st.markdown(f"**{title}**")
            st.caption(f"💰 {price}积分 | 🏷️ {rarity}")
            st.caption(f"❤️ {likes} | 🛒 {buys}")
            if status == 'on_sale':
                st.success("✅ 出售中")
            else:
                st.warning("已下架")

def render_my_collections():
    st.markdown("### 💎 我的收藏")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT p.id, p.title, p.creator, p.price_points, p.rarity, p.image_path, c.bought_at FROM poster_collections c JOIN posters p ON c.poster_id = p.id WHERE c.user = ? ORDER BY c.bought_at DESC", (st.session_state.username,))
    collections = c.fetchall()
    conn.close()
    if not collections:
        st.info("还没有收藏")
        return
    cols = st.columns(3)
    for i, col in enumerate(collections):
        poster_id, title, creator, price, rarity, image_path, bought_at = col
        with cols[i % 3]:
            if image_path and poster_os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            st.markdown(f"**{title}**")
            st.caption(f"创作者：{creator}")
            st.caption(f"🏷️ {rarity} | 💰 {price}积分")
            st.caption(f"📅 {bought_at[:10]}")

def render_poster_stats():
    st.markdown("### 📊 版图统计")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters WHERE creator = ?", (st.session_state.username,))
    total_posters = c.fetchone()[0]
    c.execute("SELECT SUM(buys) FROM posters WHERE creator = ?", (st.session_state.username,))
    total_sales = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount_points) FROM poster_earnings WHERE creator = ?", (st.session_state.username,))
    total_earnings = c.fetchone()[0] or 0
    conn.close()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("我的版图", total_posters)
    with col2:
        st.metric("总销量", total_sales)
    with col3:
        st.metric("总收益", f"{total_earnings} 积分")

# ========== UI函数 ==========
def render_auth():
    with st.sidebar:
        # 小智头像
        st.markdown("""
        <div class="sidebar-header">
            <div class="xiaozhi-avatar">🤖</div>
            <div class="xiaozhi-badge">小智 AI 助手</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown(f"### {t('user_center')}")
        if not st.session_state.get('logged_in', False):
            tab = st.radio("", [t("login"), t("register")], horizontal=True)
            if tab == t("login"):
                with st.form("login_form"):
                    username = st.text_input(t("username"))
                    password = st.text_input(t("password"), type="password")
                    if st.form_submit_button(t("login_btn"), use_container_width=True):
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
                    if st.form_submit_button(t("register_btn"), use_container_width=True):
                        if password != confirm:
                            st.error(t("password_mismatch"))
                        else:
                            ok, msg = register_user(username, password)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            st.stop()
        else:
            st.success(f"{t('welcome')}, {st.session_state.username}")
            points = get_points(st.session_state.username)
            st.markdown(f'<div class="points-badge">{t("points")}: {points}</div>', unsafe_allow_html=True)
            st.markdown("---")
            if st.button(t("logout"), use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def render_language():
    with st.sidebar:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("chinese"), use_container_width=True):
                st.session_state.language = 'zh'
                st.rerun()
        with col2:
            if st.button(t("english"), use_container_width=True):
                st.session_state.language = 'en'
                st.rerun()
        st.markdown("---")

def render_ai_assistant():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(t("ai_assistant"))
    st.info("💬 输入指令，如「剪掉前5秒」")
    user_input = st.text_input("输入指令")
    if user_input:
        st.info(f"收到指令: {user_input}")
    st.markdown('</div>', unsafe_allow_html=True)

def render_beauty_filter():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(t("beauty_filter"))
    st.info("✨ 美颜滤镜开发中")
    st.markdown('</div>', unsafe_allow_html=True)

def render_gif_export():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(t("gif_export"))
    if st.session_state.get('video_path'):
        start = st.number_input("开始时间(秒)", 0.0, 10.0, 0.0)
        duration = st.number_input("时长(秒)", 1.0, 10.0, 3.0)
        if st.button("导出为GIF"):
            out = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name
            with st.spinner(t("processing")):
                video_to_gif(st.session_state.video_path, out, start, duration)
            st.success(t("success"))
            with open(out, "rb") as f:
                st.download_button(t("download"), f, file_name="output.gif")
            cleanup_temp_files([out])
    else:
        st.info(t("upload_first"))
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 主程序 ==========
def main():
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    
    init_db()
    init_poster_tables()
    
    render_language()
    render_auth()
    
    if not st.session_state.get('logged_in', False):
        st.markdown(f"""
        <div class="main-header">
            <div class="xiaozhi-avatar" style="width: 100px; height: 100px; font-size: 60px;">🤖</div>
            <h1>{t('title')}</h1>
            <p>{t('subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("👈 请先在左侧登录或注册")
        return
    
    points = get_points(st.session_state.username)
    with st.sidebar:
        st.write(f"{t('points')}: {points}")
        st.markdown("---")
        st.markdown(f"### {t('quick_functions')}")
        
        core = [t("cut"), t("speed"), t("beauty_filter"), t("gif_export"), t("ai_assistant"), t("poster_system")]
        
        func = st.selectbox("", core)
        
        if st.session_state.get('admin_level', 0) >= 5:
            st.markdown("---")
            if st.button(t("admin_panel"), use_container_width=True):
                st.session_state.current_func = "admin"
                st.rerun()
    
    st.markdown(f"""
    <div class="main-header">
        <div class="xiaozhi-avatar" style="width: 100px; height: 100px; font-size: 60px;">🤖</div>
        <h1>{t('title')}</h1>
        <p>{t('subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 视频上传
    uploaded = st.file_uploader("上传视频", type=["mp4", "mov", "avi"])
    if uploaded:
        video_path = save_uploaded_file(uploaded)
        st.session_state.video_path = video_path
        info = get_video_info(video_path)
        if info:
            st.success(f"✅ 上传成功！时长: {info['duration']:.1f}秒")
            st.video(video_path)
    
    # 功能路由
    if func == t("cut"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(t("cut"))
        if st.session_state.get('video_path'):
            dur = get_video_info(st.session_state.video_path)["duration"]
            start = st.number_input("开始时间(秒)", 0.0, dur, 0.0)
            end = st.number_input("结束时间(秒)", 0.0, dur, min(5.0, dur))
            if st.button("开始剪切"):
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                with st.spinner(t("processing")):
                    cut_video(st.session_state.video_path, start, end, out)
                st.success(t("success"))
                with open(out, "rb") as f:
                    st.download_button(t("download"), f, file_name="cut.mp4")
                cleanup_temp_files([out])
        else:
            st.info(t("upload_first"))
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif func == t("speed"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(t("speed"))
        if st.session_state.get('video_path'):
            speed = st.number_input("速度倍数", 0.1, 5.0, 1.0, step=0.1)
            if st.button("应用变速"):
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                with st.spinner(t("processing")):
                    speed_video(st.session_state.video_path, speed, out)
                st.success(t("success"))
                with open(out, "rb") as f:
                    st.download_button(t("download"), f, file_name="speed.mp4")
                cleanup_temp_files([out])
        else:
            st.info(t("upload_first"))
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif func == t("beauty_filter"):
        render_beauty_filter()
    
    elif func == t("gif_export"):
        render_gif_export()
    
    elif func == t("ai_assistant"):
        render_ai_assistant()
    
    elif func == t("poster_system"):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        poster_tabs = st.tabs(["✨ 生成版图", "🛒 版图商城", "🖼️ 我的版图", "💎 我的收藏", "📊 版图统计"])
        with poster_tabs[0]:
            render_poster_generator()
        with poster_tabs[1]:
            render_poster_mall()
        with poster_tabs[2]:
            render_my_posters()
        with poster_tabs[3]:
            render_my_collections()
        with poster_tabs[4]:
            render_poster_stats()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
