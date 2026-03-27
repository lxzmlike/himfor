"""
小智 - 智能视频助手 v8.1
优化：桌面屏显 + 一键直达 + 语音输入
"""

import streamlit as st
import os
import hashlib
import sqlite3
import tempfile
import subprocess
import secrets
import uuid
import json
import time
import random
import cv2
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="小智 - 智能视频助手", page_icon="🤖", layout="wide")

# ========== PWA支持 ==========
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="小智">
<link rel="apple-touch-icon" href="https://img.icons8.com/color/96/000000/brain.png">
""", unsafe_allow_html=True)

# ========== 美化CSS ==========
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px 20px;
    border-radius: 30px;
    text-align: center;
    margin-bottom: 30px;
}
.main-header h1 {
    color: white;
    font-size: 2.5rem;
}
.main-header p {
    color: rgba(255,255,255,0.9);
}
/* 桌面屏显卡片 */
.dashboard-card {
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.stat-row {
    display: flex;
    justify-content: space-around;
    text-align: center;
    margin-bottom: 20px;
}
.stat-item {
    flex: 1;
}
.stat-number {
    font-size: 28px;
    font-weight: bold;
    color: #667eea;
}
.stat-label {
    font-size: 12px;
    color: #666;
}
.hot-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.hot-item {
    background: #f5f5f5;
    border-radius: 12px;
    padding: 10px;
    text-align: center;
    font-size: 12px;
    cursor: pointer;
}
.hot-item:hover {
    background: #e0e0e0;
}
.upload-card {
    background: white;
    border-radius: 24px;
    padding: 30px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.section-title {
    font-size: 24px;
    font-weight: bold;
    color: white;
    margin-bottom: 20px;
    text-align: center;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 30px;
}
.feature-card {
    background: white;
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    margin-bottom: 15px;
}
.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}
.feature-icon {
    font-size: 48px;
    margin-bottom: 10px;
}
.feature-name {
    font-size: 18px;
    font-weight: bold;
}
.feature-desc {
    font-size: 12px;
    color: #666;
}
.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 10px 20px;
    font-weight: bold;
    width: 100%;
}
.points-badge {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    display: inline-block;
}
.grid-card {
    background: white;
    border-radius: 20px;
    padding: 15px;
    margin-bottom: 20px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.grid-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# ========== 语言 ==========
LANG = {
    "zh": {
        "title": "小智 - 智能视频助手",
        "subtitle": "你的AI视频创作伙伴",
        "login": "登录",
        "register": "注册",
        "logout": "退出",
        "points": "积分",
        "upload_first": "请先上传视频"
    },
    "en": {
        "title": "XiaoZhi - AI Video Assistant",
        "subtitle": "Your AI Video Creation Partner",
        "login": "Login",
        "register": "Register",
        "logout": "Logout",
        "points": "Points",
        "upload_first": "Please upload a video first"
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

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return {"duration": total_frames/fps if fps > 0 else 0}

def cut_video(input_path, start, end, output_path):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-to", str(end), "-c", "copy", output_path])

def speed_video(input_path, speed, output_path):
    subprocess.run(["ffmpeg", "-i", input_path, "-filter:v", f"setpts={1/speed}*PTS", "-c:a", "aac", output_path])

def video_to_gif(input_path, output_path, start=0, duration=5):
    subprocess.run(["ffmpeg", "-i", input_path, "-ss", str(start), "-t", str(duration), "-vf", "fps=10,scale=320:-1", output_path])

# ========== 数据库 ==========
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT,
        salt TEXT,
        points INTEGER DEFAULT 100,
        admin_level INTEGER DEFAULT 0,
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
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pwd_hash, salt

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, salt, points, admin_level FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, "用户不存在"
    stored_hash, salt, points, admin_level = row
    input_hash, _ = hash_password(password, salt)
    if input_hash == stored_hash:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.points = points
        st.session_state.admin_level = admin_level
        st.session_state.remember_me = True
        return True, "登录成功"
    return False, "密码错误"

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return False, "用户名已存在"
    pwd_hash, salt = hash_password(password)
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    admin_level = 5 if count == 0 else 0
    c.execute("INSERT INTO users (username, password_hash, salt, points, admin_level) VALUES (?, ?, ?, 100, ?)", 
              (username, pwd_hash, salt, admin_level))
    conn.commit()
    conn.close()
    return True, "注册成功"

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

# ========== 版图系统 ==========
POSTER_DIR = "poster_images"
os.makedirs(POSTER_DIR, exist_ok=True)

def init_poster_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator TEXT,
        title TEXT,
        description TEXT,
        price_points INTEGER DEFAULT 100,
        rarity TEXT DEFAULT '普通',
        image_path TEXT,
        likes INTEGER DEFAULT 0,
        buys INTEGER DEFAULT 0,
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

def save_poster_image(frame, poster_id):
    height, width = frame.shape[:2]
    max_size = 300
    if width > max_size:
        ratio = max_size / width
        new_width = max_size
        new_height = int(height * ratio)
        frame = cv2.resize(frame, (new_width, new_height))
    filepath = os.path.join(POSTER_DIR, f"{poster_id}.jpg")
    cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return filepath

def extract_frame_from_video(video_path, poster_id):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_frame = total_frames // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return save_poster_image(frame, poster_id)
    return None

def render_poster_generator():
    st.markdown("### 🎨 生成版图")
    if not st.session_state.get('video_path'):
        st.info("请先上传视频")
        return
    video_path = st.session_state.video_path
    st.video(video_path)
    title = st.text_input("版图标题")
    price = st.number_input("价格（积分）", min_value=10, value=100)
    rarity = st.selectbox("稀有度", ["普通", "稀有", "史诗", "传说"])
    if st.button("✨ 生成版图"):
        if title:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO posters (creator, title, price_points, rarity) VALUES (?, ?, ?, ?)",
                      (st.session_state.username, title, price, rarity))
            poster_id = c.lastrowid
            conn.commit()
            image_path = extract_frame_from_video(video_path, poster_id)
            if image_path:
                c.execute("UPDATE posters SET image_path = ? WHERE id = ?", (image_path, poster_id))
                conn.commit()
                st.success(f"✅ 版图「{title}」生成成功！")
                st.balloons()
            conn.close()

def render_poster_mall():
    st.markdown("### 🛒 版图商城")
    if 'poster_page' not in st.session_state:
        st.session_state.poster_page = 1
    page_size = 12
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters")
    total = c.fetchone()[0]
    total_pages = (total + page_size - 1) // page_size
    offset = (st.session_state.poster_page - 1) * page_size
    c.execute("SELECT id, creator, title, price_points, rarity, likes, buys, image_path FROM posters ORDER BY created_at DESC LIMIT ? OFFSET ?", (page_size, offset))
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("暂无版图")
        return
    cols = st.columns(4)
    for i, poster in enumerate(posters):
        poster_id, creator, title, price, rarity, likes, buys, image_path = poster
        with cols[i % 4]:
            st.markdown('<div class="grid-card">', unsafe_allow_html=True)
            if image_path and os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            st.markdown(f"**{title[:20]}**")
            st.caption(f"👤 {creator} | 🏷️ {rarity}")
            st.caption(f"💰 {price}积分 | ❤️ {likes} | 🛒 {buys}")
            if st.button(f"购买", key=f"buy_poster_{poster_id}"):
                if spend_points(st.session_state.username, price, f"购买版图{title}"):
                    conn2 = sqlite3.connect('users.db')
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
                else:
                    st.error("积分不足")
            st.markdown('</div>', unsafe_allow_html=True)
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
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT title, price_points, rarity, likes, buys, image_path FROM posters WHERE creator = ?", (st.session_state.username,))
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("还没有版图")
        return
    cols = st.columns(3)
    for i, poster in enumerate(posters):
        title, price, rarity, likes, buys, image_path = poster
        with cols[i % 3]:
            if image_path and os.path.exists(image_path):
                st.image(image_path, width=150)
            st.markdown(f"**{title}** | 💰 {price}积分 | 🏷️ {rarity}")
            st.caption(f"❤️ {likes} | 🛒 {buys}")

def render_my_collections():
    st.markdown("### 💎 我的收藏")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT p.title, p.creator, p.price_points, p.rarity, p.image_path FROM poster_collections c JOIN posters p ON c.poster_id = p.id WHERE c.user = ?", (st.session_state.username,))
    collections = c.fetchall()
    conn.close()
    if not collections:
        st.info("还没有收藏")
        return
    cols = st.columns(3)
    for i, col in enumerate(collections):
        title, creator, price, rarity, image_path = col
        with cols[i % 3]:
            if image_path and os.path.exists(image_path):
                st.image(image_path, width=150)
            st.markdown(f"**{title}** | 创作者：{creator} | 💰 {price}积分 | 🏷️ {rarity}")

def render_poster_stats():
    st.markdown("### 📊 版图统计")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters WHERE creator = ?", (st.session_state.username,))
    total = c.fetchone()[0]
    c.execute("SELECT SUM(buys) FROM posters WHERE creator = ?", (st.session_state.username,))
    sales = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount_points) FROM poster_earnings WHERE creator = ?", (st.session_state.username,))
    earnings = c.fetchone()[0] or 0
    conn.close()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("我的版图", total)
    with col2:
        st.metric("总销量", sales)
    with col3:
        st.metric("总收益", f"{earnings} 积分")

# ========== 壁纸系统 ==========
WALLPAPER_DIR = "wallpapers"
os.makedirs(WALLPAPER_DIR, exist_ok=True)

def init_wallpaper_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wallpapers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator TEXT,
        title TEXT,
        description TEXT,
        image_path TEXT,
        price_points INTEGER DEFAULT 100,
        category TEXT DEFAULT '其他',
        signature_info TEXT,
        likes INTEGER DEFAULT 0,
        buys INTEGER DEFAULT 0,
        status TEXT DEFAULT 'on_sale',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wallpaper_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        wallpaper_id INTEGER,
        price_points INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wallpaper_earnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator TEXT,
        wallpaper_id INTEGER,
        buyer TEXT,
        amount_points INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_signature_to_image(image_path, signature_info, output_path):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        font_size = max(12, int(width / 35))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        lines = []
        if signature_info.get("custom"):
            lines.append(signature_info["custom"])
        if signature_info.get("title"):
            lines.append(signature_info["title"])
        lines.append(f"@{signature_info.get('creator', '小智')}")
        if signature_info.get("date"):
            lines.append(signature_info["date"])
        if signature_info.get("code"):
            lines.append(signature_info["code"])
        if not lines:
            img.save(output_path, quality=95)
            return
        line_height = font_size + 5
        text_height = len(lines) * line_height + 10
        text_width = max([draw.textlength(line, font=font) for line in lines]) + 20
        padding = 15
        pos_map = {
            "右下角": (width - text_width - padding, height - text_height - padding),
            "左下角": (padding, height - text_height - padding),
            "左上角": (padding, padding),
            "右上角": (width - text_width - padding, padding)
        }
        position = pos_map.get(signature_info.get("position", "右下角"), pos_map["右下角"])
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [position[0] - 5, position[1] - 5, 
             position[0] + text_width + 5, position[1] + text_height + 5],
            fill=(0, 0, 0, 128)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay)
        draw = ImageDraw.Draw(img)
        y = position[1] + 5
        for line in lines:
            draw.text((position[0] + 5, y), line, fill=(255, 255, 255), font=font)
            y += line_height
        img.convert('RGB').save(output_path, quality=95)
    except Exception as e:
        import shutil
        shutil.copy(image_path, output_path)

def save_wallpaper_image(uploaded_file, signature_info):
    ext = uploaded_file.name.split('.')[-1]
    temp_path = os.path.join(WALLPAPER_DIR, f"temp_{uuid.uuid4().hex}.{ext}")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    filename = f"{uuid.uuid4().hex}.jpg"
    final_path = os.path.join(WALLPAPER_DIR, filename)
    if signature_info.get("enable", True):
        add_signature_to_image(temp_path, signature_info, final_path)
    else:
        import shutil
        shutil.copy(temp_path, final_path)
    try:
        os.remove(temp_path)
    except:
        pass
    return final_path

def render_wallpaper_generator():
    st.markdown("### 🖼️ 生成壁纸")
    uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], key="wallpaper_upload")
    if uploaded_file:
        st.image(uploaded_file, caption="预览", use_column_width=True)
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("壁纸标题")
        with col2:
            category = st.selectbox("分类", ["风景", "人物", "抽象", "动漫", "科技", "其他"])
        price = st.number_input("价格（积分）", min_value=10, value=100)
        st.markdown("---")
        st.markdown("### ✍️ 个性签名")
        col1, col2, col3 = st.columns(3)
        with col1:
            enable_sig = st.checkbox("✅ 添加签名", value=True)
        with col2:
            enable_title = st.checkbox("📝 添加标题", value=True)
        with col3:
            enable_date = st.checkbox("📅 添加日期", value=True)
        custom_sig = st.text_input("💬 自定义签名（可选）")
        sig_position = st.selectbox("📍 签名位置", ["右下角", "左下角", "左上角", "右上角"])
        if st.button("✨ 上架壁纸"):
            if title:
                code = f"XZ-{int(time.time()) % 10000:04d}-{random.randint(100, 999)}"
                sig_info = {
                    "enable": enable_sig,
                    "title": title if enable_title else "",
                    "date": time.strftime("%Y.%m.%d") if enable_date else "",
                    "code": code,
                    "custom": custom_sig,
                    "position": sig_position,
                    "creator": st.session_state.username
                }
                image_path = save_wallpaper_image(uploaded_file, sig_info)
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("INSERT INTO wallpapers (creator, title, price_points, category, image_path, signature_info) VALUES (?, ?, ?, ?, ?, ?)",
                          (st.session_state.username, title, price, category, image_path, json.dumps(sig_info)))
                conn.commit()
                conn.close()
                st.success(f"✅ 壁纸「{title}」上架成功！")
                st.balloons()

def render_wallpaper_mall():
    st.markdown("### 🛒 壁纸商城")
    if 'wallpaper_page' not in st.session_state:
        st.session_state.wallpaper_page = 1
    page_size = 12
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    categories = ["全部", "风景", "人物", "抽象", "动漫", "科技", "其他"]
    selected_cat = st.selectbox("分类", categories, key="wallpaper_cat")
    if selected_cat == "全部":
        c.execute("SELECT COUNT(*) FROM wallpapers WHERE status = 'on_sale'")
    else:
        c.execute("SELECT COUNT(*) FROM wallpapers WHERE status = 'on_sale' AND category = ?", (selected_cat,))
    total = c.fetchone()[0]
    total_pages = (total + page_size - 1) // page_size
    offset = (st.session_state.wallpaper_page - 1) * page_size
    if selected_cat == "全部":
        c.execute("SELECT id, creator, title, price_points, category, likes, buys, image_path FROM wallpapers WHERE status = 'on_sale' ORDER BY created_at DESC LIMIT ? OFFSET ?", (page_size, offset))
    else:
        c.execute("SELECT id, creator, title, price_points, category, likes, buys, image_path FROM wallpapers WHERE status = 'on_sale' AND category = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", (selected_cat, page_size, offset))
    wallpapers = c.fetchall()
    conn.close()
    if not wallpapers:
        st.info("暂无壁纸")
        return
    cols = st.columns(4)
    for i, wp in enumerate(wallpapers):
        wp_id, creator, title, price, category, likes, buys, image_path = wp
        with cols[i % 4]:
            st.markdown('<div class="grid-card">', unsafe_allow_html=True)
            if image_path and os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            st.markdown(f"**{title[:20]}**")
            st.caption(f"👤 {creator} | 📂 {category}")
            st.caption(f"💰 {price}积分 | ❤️ {likes} | 🛒 {buys}")
            if st.button(f"购买", key=f"buy_wall_{wp_id}"):
                if spend_points(st.session_state.username, price, f"购买壁纸{title}"):
                    conn2 = sqlite3.connect('users.db')
                    c2 = conn2.cursor()
                    c2.execute("INSERT INTO wallpaper_purchases (user, wallpaper_id, price_points) VALUES (?, ?, ?)",
                               (st.session_state.username, wp_id, price))
                    c2.execute("UPDATE wallpapers SET buys = buys + 1 WHERE id = ?", (wp_id,))
                    c2.execute("INSERT INTO wallpaper_earnings (creator, wallpaper_id, buyer, amount_points) VALUES (?, ?, ?, ?)",
                               (creator, wp_id, st.session_state.username, price))
                    conn2.commit()
                    conn2.close()
                    creator_points = int(price * 0.8)
                    add_points(creator, creator_points, f"壁纸{title}被购买")
                    st.success(f"购买成功！{creator}获得{creator_points}积分")
                    st.rerun()
                else:
                    st.error("积分不足")
            st.markdown('</div>', unsafe_allow_html=True)
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            col_prev, col_page, col_next = st.columns(3)
            if st.session_state.wallpaper_page > 1:
                if col_prev.button("◀", key="wall_prev"):
                    st.session_state.wallpaper_page -= 1
                    st.rerun()
            col_page.markdown(f"<div style='text-align:center'>{st.session_state.wallpaper_page}/{total_pages}</div>", unsafe_allow_html=True)
            if st.session_state.wallpaper_page < total_pages:
                if col_next.button("▶", key="wall_next"):
                    st.session_state.wallpaper_page += 1
                    st.rerun()

def render_my_wallpapers():
    st.markdown("### 🖼️ 我的壁纸")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    st.markdown("#### 📤 我创作的")
    c.execute("SELECT title, price_points, category, likes, buys, image_path FROM wallpapers WHERE creator = ?", (st.session_state.username,))
    my_wallpapers = c.fetchall()
    if my_wallpapers:
        cols = st.columns(3)
        for i, wp in enumerate(my_wallpapers):
            title, price, category, likes, buys, image_path = wp
            with cols[i % 3]:
                if image_path and os.path.exists(image_path):
                    st.image(image_path, width=150)
                st.markdown(f"**{title}** | 💰 {price}积分 | 📂 {category}")
                st.caption(f"❤️ {likes} | 🛒 {buys}")
    else:
        st.info("还没有创作壁纸")
    st.markdown("#### 💎 我购买的")
    c.execute("SELECT w.title, w.creator, w.price_points, w.category, w.image_path, p.created_at FROM wallpaper_purchases p JOIN wallpapers w ON p.wallpaper_id = w.id WHERE p.user = ? ORDER BY p.created_at DESC", (st.session_state.username,))
    bought = c.fetchall()
    if bought:
        cols = st.columns(3)
        for i, item in enumerate(bought):
            title, creator, price, category, image_path, bought_at = item
            with cols[i % 3]:
                if image_path and os.path.exists(image_path):
                    st.image(image_path, width=150)
                st.markdown(f"**{title}**")
                st.caption(f"创作者：{creator} | 💰 {price}积分 | 📂 {category}")
                st.caption(f"📅 {bought_at[:10]}")
    else:
        st.info("还没有购买壁纸")
    conn.close()

def render_wallpaper_stats():
    st.markdown("### 📊 壁纸统计")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM wallpapers WHERE creator = ?", (st.session_state.username,))
    total = c.fetchone()[0]
    c.execute("SELECT SUM(buys) FROM wallpapers WHERE creator = ?", (st.session_state.username,))
    sales = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount_points) FROM wallpaper_earnings WHERE creator = ?", (st.session_state.username,))
    earnings = c.fetchone()[0] or 0
    conn.close()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("我的壁纸", total)
    with col2:
        st.metric("总销量", sales)
    with col3:
        st.metric("总收益", f"{earnings} 积分")

# ========== 摄像头功能 ==========
def save_temp_image(uploaded_file):
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join("temp_images", filename)
    os.makedirs("temp_images", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def render_camera():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📷 摄像头拍摄")
    st.markdown("拍照后可直接生成版图或壁纸")
    camera_image = st.camera_input("点击拍照", key="camera_shot")
    if camera_image:
        st.image(camera_image, caption="拍摄的照片", use_column_width=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎨 生成版图"):
                image_path = save_temp_image(camera_image)
                st.session_state.camera_image = image_path
                st.success("✅ 照片已保存，可以生成版图了！")
        with col2:
            if st.button("🖼️ 制作壁纸"):
                image_path = save_temp_image(camera_image)
                st.session_state.wallpaper_image = image_path
                st.success("✅ 照片已保存，可以制作壁纸了！")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 公益系统 ==========
WELFARE_PROJECTS = [
    {"id": 1, "name": "乡村儿童视频课", "points": 100, "icon": "🏫", "impact": "支持1个孩子上一节视频课"},
    {"id": 2, "name": "环保视频计划", "points": 50, "icon": "🌍", "impact": "支持1个环保视频拍摄"},
    {"id": 3, "name": "残障创作者支持", "points": 200, "icon": "❤️", "impact": "支持1位残障创作者"},
    {"id": 4, "name": "动物保护视频", "points": 30, "icon": "🐕", "impact": "帮助1只流浪动物"},
]

WELFARE_BADGES = [
    {"name": "爱心萌芽", "points": 100, "icon": "🌱"},
    {"name": "爱心使者", "points": 500, "icon": "🌟"},
    {"name": "爱心大使", "points": 1000, "icon": "💎"},
    {"name": "公益之星", "points": 5000, "icon": "🏆"},
    {"name": "公益传奇", "points": 10000, "icon": "👑"},
]

def init_welfare_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS welfare_donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        project_id INTEGER,
        points INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS welfare_points (
        user TEXT PRIMARY KEY,
        total_donated INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def get_welfare_points(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT total_donated FROM welfare_points WHERE user = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_welfare_points(username, points, project_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO welfare_points (user, total_donated) VALUES (?, 0)", (username,))
    c.execute("UPDATE welfare_points SET total_donated = total_donated + ? WHERE user = ?", (points, username))
    c.execute("INSERT INTO welfare_donations (user, project_id, points) VALUES (?, ?, ?)", (username, project_id, points))
    conn.commit()
    conn.close()

def render_welfare():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🌍 公益积分")
    total_donated = get_welfare_points(st.session_state.username)
    st.markdown(f"**累计捐赠：{total_donated} 积分**")
    badges = []
    for badge in WELFARE_BADGES:
        if total_donated >= badge["points"]:
            badges.append(badge)
    if badges:
        st.markdown("**🏅 已获得勋章**")
        cols = st.columns(len(badges))
        for i, badge in enumerate(badges):
            with cols[i]:
                st.markdown(f"<div style='text-align:center'><div style='font-size:40px'>{badge['icon']}</div><div>{badge['name']}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🌱 公益项目")
    for project in WELFARE_PROJECTS:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            st.markdown(f"<div style='font-size:40px'>{project['icon']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{project['name']}**")
            st.caption(project['impact'])
        with col3:
            st.markdown(f"💰 {project['points']}积分")
            if st.button(f"捐赠", key=f"donate_{project['id']}"):
                if spend_points(st.session_state.username, project['points'], f"公益捐赠-{project['name']}"):
                    add_welfare_points(st.session_state.username, project['points'], project['id'])
                    st.success(f"✅ 感谢你的爱心！已捐赠 {project['points']} 积分")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("积分不足")
        st.markdown("---")
    st.markdown("### 🏆 公益排行榜")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user, total_donated FROM welfare_points ORDER BY total_donated DESC LIMIT 10")
    leaders = c.fetchall()
    if leaders:
        for i, leader in enumerate(leaders):
            st.markdown(f"{i+1}. {leader[0]} - 累计捐赠 {leader[1]} 积分")
    else:
        st.info("暂无公益记录")
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 奖池金系统 ==========
def init_jackpot_tables():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jackpot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        total_points INTEGER DEFAULT 0,
        distributed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS jackpot_winners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        winner TEXT,
        category TEXT,
        rank INTEGER,
        points INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def get_current_jackpot():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    current_month = time.strftime("%Y-%m")
    c.execute("SELECT total_points FROM jackpot WHERE month = ?", (current_month,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def render_jackpot():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💰 小智奖池金")
    current_jackpot = get_current_jackpot()
    st.markdown(f"**本月奖池金：{current_jackpot} 积分**")
    st.markdown("---")
    st.markdown("### 📊 奖池金来源")
    st.markdown("""
    | 来源 | 比例 | 说明 |
    |-----|------|------|
    | 版图/壁纸交易 | 10% | 平台抽成的50% |
    | 广告收益 | 20% | 广告收益的40% |
    | 创作者认证 | 100% | 认证费用 |
    """)
    st.markdown("---")
    st.markdown("### 🏆 本月排行榜")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🏅 创作者榜**")
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT creator, SUM(amount_points) as total FROM poster_earnings GROUP BY creator ORDER BY total DESC LIMIT 5")
        creators = c.fetchall()
        if creators:
            for i, creator in enumerate(creators):
                st.markdown(f"{i+1}. {creator[0]} - {creator[1]}积分")
        else:
            st.info("暂无数据")
    with col2:
        st.markdown("**🌱 公益榜**")
        c.execute("SELECT user, total_donated FROM welfare_points ORDER BY total_donated DESC LIMIT 5")
        donors = c.fetchall()
        if donors:
            for i, donor in enumerate(donors):
                st.markdown(f"{i+1}. {donor[0]} - {donor[1]}积分")
        else:
            st.info("暂无数据")
        conn.close()
    st.markdown("---")
    st.markdown("### 🎁 奖池金分配规则")
    st.markdown("""
    - **50%** 分配给创作者榜Top5
    - **30%** 分配给公益榜Top5
    - **10%** 分配给新星榜Top4
    - **10%** 滚入下月奖池
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 界面函数 ==========
def render_auth():
    with st.sidebar:
        st.markdown("### 👤 用户中心")
        if not st.session_state.get('logged_in', False):
            tab = st.radio("", ["登录", "注册"], horizontal=True)
            if tab == "登录":
                username = st.text_input("用户名")
                password = st.text_input("密码", type="password")
                if st.button("登录"):
                    ok, msg = login_user(username, password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                username = st.text_input("用户名")
                password = st.text_input("密码", type="password")
                confirm = st.text_input("确认密码", type="password")
                if st.button("注册"):
                    if password != confirm:
                        st.error("两次密码不一致")
                    else:
                        ok, msg = register_user(username, password)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            st.stop()
        else:
            points = get_points(st.session_state.username)
            st.success(f"欢迎，{st.session_state.username}")
            st.markdown(f'<div class="points-badge">⭐ 积分：{points}</div>', unsafe_allow_html=True)
            if st.button("退出登录"):
                st.session_state.clear()
                st.rerun()

def render_language():
    with st.sidebar:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("中文"):
                st.session_state.language = 'zh'
                st.rerun()
        with col2:
            if st.button("English"):
                st.session_state.language = 'en'
                st.rerun()

def render_ai_assistant():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🤖 小智AI助手")
    
    # 输入框 + 语音按钮
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("", placeholder="💬 试试说：剪掉前5秒、加速2倍、导出GIF", key="ai_input")
    with col2:
        # 语音输入按钮（点击调用语音识别）
        if st.button("🎤", key="voice_btn", help="点击说话"):
            # 使用 JavaScript 调用浏览器语音识别
            st.markdown("""
            <script>
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'zh-CN';
            recognition.start();
            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                document.querySelector('input[data-testid="stTextInput"]').value = text;
                // 模拟提交
                const btn = document.querySelector('button[kind="primary"]');
                if (btn) btn.click();
            };
            </script>
            """, unsafe_allow_html=True)
            st.info("🎤 正在听你说话...")
    
    if user_input:
        if "剪" in user_input or "切" in user_input:
            st.success("✅ 已识别：剪切视频")
            # 这里可以自动执行剪切，简化流程
        elif "速" in user_input:
            st.success("✅ 已识别：调整速度")
        elif "GIF" in user_input or "动图" in user_input:
            st.success("✅ 已识别：导出GIF")
        else:
            st.info(f"收到：{user_input}")
    st.markdown('</div>', unsafe_allow_html=True)

def render_beauty_filter():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("✨ 美颜滤镜")
    st.info("美颜滤镜开发中，敬请期待")
    st.markdown('</div>', unsafe_allow_html=True)

def render_gif_export():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎞️ 导出GIF")
    if st.session_state.get('video_path'):
        start = st.number_input("开始时间(秒)", 0.0, 10.0, 0.0)
        duration = st.number_input("时长(秒)", 1.0, 10.0, 3.0)
        if st.button("导出为GIF"):
            out = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name
            video_to_gif(st.session_state.video_path, out, start, duration)
            with open(out, "rb") as f:
                st.download_button("下载", f, file_name="output.gif")
    else:
        st.info(t("upload_first"))
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 主程序 ==========
def main():
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    
    # 自动登录
    if st.session_state.get('remember_me', False):
        if 'username' in st.session_state:
            st.session_state.logged_in = True
    
    init_db()
    init_poster_tables()
    init_wallpaper_tables()
    init_welfare_tables()
    init_jackpot_tables()
    
    render_language()
    render_auth()
    
    if not st.session_state.get('logged_in', False):
        st.markdown("""
        <div class="main-header">
            <div style="font-size: 60px;">🤖</div>
            <h1>小智 - 智能视频助手</h1>
            <p>你的AI视频创作伙伴</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("👈 请先在左侧登录或注册")
        return
    
    # ========== 桌面屏显 ==========
    points = get_points(st.session_state.username)
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters WHERE creator = ?", (st.session_state.username,))
    poster_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM wallpapers WHERE creator = ?", (st.session_state.username,))
    wallpaper_count = c.fetchone()[0]
    conn.close()
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<div class="stat-row">', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-item"><div class="stat-number">{points}</div><div class="stat-label">积分</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-item"><div class="stat-number">{poster_count + wallpaper_count}</div><div class="stat-label">作品数</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-item"><div class="stat-number">{poster_count}</div><div class="stat-label">版图</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-item"><div class="stat-number">{wallpaper_count}</div><div class="stat-label">壁纸</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 热门推荐（最近上架的3个版图/壁纸）
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT title, price_points FROM posters ORDER BY created_at DESC LIMIT 3")
    hot_posters = c.fetchall()
    c.execute("SELECT title, price_points FROM wallpapers ORDER BY created_at DESC LIMIT 3")
    hot_wallpapers = c.fetchall()
    conn.close()
    
    if hot_posters or hot_wallpapers:
        st.markdown('<div class="stat-label" style="margin-bottom: 10px;">🔥 热门推荐</div>', unsafe_allow_html=True)
        st.markdown('<div class="hot-grid">', unsafe_allow_html=True)
        for p in hot_posters[:2]:
            st.markdown(f'<div class="hot-item">🖼️ {p[0]}<br>{p[1]}积分</div>', unsafe_allow_html=True)
        for w in hot_wallpapers[:2]:
            st.markdown(f'<div class="hot-item">🎨 {w[0]}<br>{w[1]}积分</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== 上传区域 ==========
    st.markdown("""
    <div class="upload-card">
        <div style="font-size: 48px;">📤</div>
        <h3>上传视频</h3>
        <p>拖拽文件到这里，或点击浏览</p>
        <p style="color: #999;">支持 MP4、MOV、AVI 格式</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader("", type=["mp4", "mov", "avi"], label_visibility="collapsed")
    
    if uploaded:
        video_path = save_uploaded_file(uploaded)
        st.session_state.video_path = video_path
        st.video(video_path)
        st.success("✅ 上传成功！")
    
    # ========== 功能卡片（一键直达）==========
    st.markdown('<div class="section-title">🎬 视频创作工坊</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 剪切视频（一键直达）
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">✂️</div>
            <div class="feature-name">剪切视频</div>
            <div class="feature-desc">剪掉不要的片段</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开始剪切", key="cut_btn"):
            if st.session_state.get('video_path'):
                dur = get_video_info(st.session_state.video_path)["duration"]
                with st.expander("设置剪切时间", expanded=True):
                    start = st.number_input("开始(秒)", 0.0, dur, 0.0)
                    end = st.number_input("结束(秒)", 0.0, dur, min(5.0, dur))
                    if st.button("确认剪切"):
                        out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                        cut_video(st.session_state.video_path, start, end, out)
                        with open(out, "rb") as f:
                            st.download_button("下载", f, file_name="cut.mp4")
            else:
                st.warning("请先上传视频")
    
    # 视频变速（一键直达）
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-name">视频变速</div>
            <div class="feature-desc">快慢随心调</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("调整速度", key="speed_btn"):
            if st.session_state.get('video_path'):
                with st.expander("设置速度倍数", expanded=True):
                    speed = st.number_input("倍数", 0.5, 2.0, 1.0, step=0.1)
                    if st.button("确认变速"):
                        out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                        speed_video(st.session_state.video_path, speed, out)
                        with open(out, "rb") as f:
                            st.download_button("下载", f, file_name="speed.mp4")
            else:
                st.warning("请先上传视频")
    
    # 导出GIF（一键直达）
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎞️</div>
            <div class="feature-name">导出GIF</div>
            <div class="feature-desc">制作动图表情</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("导出GIF", key="gif_btn"):
            if st.session_state.get('video_path'):
                with st.expander("设置GIF参数", expanded=True):
                    start = st.number_input("开始时间(秒)", 0.0, 10.0, 0.0)
                    duration = st.number_input("时长(秒)", 1.0, 10.0, 3.0)
                    if st.button("确认导出"):
                        out = tempfile.NamedTemporaryFile(suffix=".gif", delete=False).name
                        video_to_gif(st.session_state.video_path, out, start, duration)
                        with open(out, "rb") as f:
                            st.download_button("下载", f, file_name="output.gif")
            else:
                st.info(t("upload_first"))
    
    # 美颜滤镜（占位）
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">✨</div>
            <div class="feature-name">美颜滤镜</div>
            <div class="feature-desc">让视频更美</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开启美颜", key="beauty_btn"):
            render_beauty_filter()
    
    # ========== AI创作生态 ==========
    st.markdown('<div class="section-title">🤖 AI创作生态</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-name">小智AI助手</div>
            <div class="feature-desc">说人话就能剪</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("对话小智", key="ai_btn"):
            render_ai_assistant()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <div class="feature-name">版图系统</div>
            <div class="feature-desc">创作即资产</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入版图", key="poster_btn"):
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
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <div class="feature-name">壁纸系统</div>
            <div class="feature-desc">设计即资产</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入壁纸", key="wallpaper_btn"):
            wallpaper_tabs = st.tabs(["🎨 创作壁纸", "🛒 壁纸商城", "🖼️ 我的壁纸", "📊 壁纸统计"])
            with wallpaper_tabs[0]:
                render_wallpaper_generator()
            with wallpaper_tabs[1]:
                render_wallpaper_mall()
            with wallpaper_tabs[2]:
                render_my_wallpapers()
            with wallpaper_tabs[3]:
                渲染_壁纸_统计()
    
    随着第四栏:
街道减价("""
< div class= "功能卡">
< div class="feature-icon " >📷</div >
< div class= "功能名称">摄像头</div >
< div class= "功能——desc " >拍照创作</div >
</div >
        """，unsafe_allow_html=真实的)
        如果街道按钮("打开摄像头"，键="相机_btn "):
            渲染_相机()
    
    # ========== 公益与奖池 ==========
街道减价(< div class="section-title " >💚 公益与奖池</div > '，unsafe_allow_html=真实的)
    
col1，col2 = st .列(2)
    
    随着列1:
街道减价("""
< div class= "功能卡">
< div class="feature-icon " >🌍</div >
< div class= "功能名称">公益积分</div >
< div class= "功能-desc " >用积分做公益,得勋章</div >
</div >
        """，unsafe_allow_html=真实的)
        如果街道按钮("做公益"，键="福利_btn "):
            渲染_福利()
    
    随着第二栏:
街道减价("""
< div class= "功能卡">
< div class="feature-icon " >💰</div >
< div class= "功能名称">奖池金</div >
< div class= "功能-desc " >每月奖励创作者和公益者</div >
</div >
        """，unsafe_allow_html=真实的)
        如果街道按钮("查看奖池"，键="头奖_btn "):
            渲染_头奖()

如果__name__ ==" __main__ ":
    主要的()
