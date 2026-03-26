"""
小智 - 智能视频助手 v6.0
完整版：用户系统 + 视频剪辑 + 版图系统 + 小智AI + 积分系统
"""

import streamlit as st
import os
import hashlib
import sqlite3
import tempfile
import subprocess
import secrets
import cv2

st.set_page_config(page_title="小智 - 智能视频助手", page_icon="🤖", layout="wide")

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
.upload-card {
    background: white;
    border-radius: 24px;
    padding: 40px;
    text-align: center;
    margin-bottom: 30px;
}
.section-title {
    font-size: 24px;
    font-weight: bold;
    color: white;
    margin-bottom: 20px;
    text-align: center;
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
        points INTEGER DEFAULT 100
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
    c.execute("SELECT password_hash, salt, points FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False, "用户不存在"
    stored_hash, salt, points = row
    input_hash, _ = hash_password(password, salt)
    if input_hash == stored_hash:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.points = points
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
    c.execute("INSERT INTO users (username, password_hash, salt, points) VALUES (?, ?, ?, 100)", 
              (username, pwd_hash, salt))
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

def add_points(username, amount):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE username=?", (amount, username))
    conn.commit()
    conn.close()

def spend_points(username, points):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if not row or row[0] < points:
        conn.close()
        return False
    c.execute("UPDATE users SET points = points - ? WHERE username=?", (points, username))
    conn.commit()
    conn.close()
    return True

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
        price_points INTEGER DEFAULT 100,
        rarity TEXT DEFAULT '普通',
        image_path TEXT,
        buys INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS poster_collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        poster_id INTEGER,
        bought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def render_poster_generator():
    st.markdown("### 🎨 生成版图")
    if not st.session_state.get('video_path'):
        st.info("请先上传视频")
        return
    video_path = st.session_state.video_path
    st.video(video_path)
    title = st.text_input("版图标题")
    price = st.number_input("价格（积分）", min_value=10, value=100)
    if st.button("✨ 生成版图"):
        if title:
            conn = poster_sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO posters (creator, title, price_points) VALUES (?, ?, ?)",
                      (st.session_state.username, title, price))
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
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, creator, title, price_points, rarity, image_path, buys FROM posters ORDER BY created_at DESC LIMIT 12")
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("暂无版图")
        return
    cols = st.columns(3)
    for i, poster in enumerate(posters):
        poster_id, creator, title, price, rarity, image_path, buys = poster
        with cols[i % 3]:
            if image_path and poster_os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
            st.markdown(f"**{title}**")
            st.caption(f"创作者：{creator}")
            st.caption(f"💰 {price}积分 | 🏷️ {rarity}")
            if st.button(f"购买", key=f"buy_{poster_id}"):
                if spend_points(st.session_state.username, price):
                    conn2 = poster_sqlite3.connect('users.db')
                    c2 = conn2.cursor()
                    c2.execute("INSERT INTO poster_collections (user, poster_id) VALUES (?, ?)", (st.session_state.username, poster_id))
                    c2.execute("UPDATE posters SET buys = buys + 1 WHERE id = ?", (poster_id,))
                    conn2.commit()
                    conn2.close()
                    add_points(creator, int(price * 0.8))
                    st.success(f"购买成功！{creator}获得{int(price*0.8)}积分")
                    st.rerun()
                else:
                    st.error("积分不足")

def render_my_posters():
    st.markdown("### 🖼️ 我的版图")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, price_points, rarity, image_path, buys FROM posters WHERE creator = ?", (st.session_state.username,))
    posters = c.fetchall()
    conn.close()
    if not posters:
        st.info("还没有版图")
        return
    for poster in posters:
        poster_id, title, price, rarity, image_path, buys = poster
        if image_path and poster_os.path.exists(image_path):
            st.image(image_path, width=200)
        st.markdown(f"**{title}** | 💰 {price}积分 | 🏷️ {rarity} | 🛒 {buys}次购买")

def render_my_collections():
    st.markdown("### 💎 我的收藏")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT p.title, p.creator, p.price_points, p.rarity, p.image_path FROM poster_collections c JOIN posters p ON c.poster_id = p.id WHERE c.user = ?", (st.session_state.username,))
    collections = c.fetchall()
    conn.close()
    if not collections:
        st.info("还没有收藏")
        return
    for col in collections:
        title, creator, price, rarity, image_path = col
        if image_path and poster_os.path.exists(image_path):
            st.image(image_path, width=200)
        st.markdown(f"**{title}** | 创作者：{creator} | 💰 {price}积分 | 🏷️ {rarity}")

def render_poster_stats():
    st.markdown("### 📊 版图统计")
    conn = poster_sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posters WHERE creator = ?", (st.session_state.username,))
    total = c.fetchone()[0]
    c.execute("SELECT SUM(buys) FROM posters WHERE creator = ?", (st.session_state.username,))
    sales = c.fetchone()[0] or 0
    conn.close()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("我的版图", total)
    with col2:
        st.metric("总销量", sales)

def render_ai_assistant():
    st.markdown("### 🤖 小智AI助手")
    st.info("💬 试试说：剪掉前5秒、加速2倍、导出GIF")
    user_input = st.text_input("输入指令")
    if user_input:
        if "剪" in user_input or "切" in user_input:
            st.success("✅ 已识别：剪切视频")
        elif "速" in user_input:
            st.success("✅ 已识别：调整速度")
        elif "GIF" in user_input or "动图" in user_input:
            st.success("✅ 已识别：导出GIF")
        else:
            st.info(f"收到：{user_input}")

def render_beauty_filter():
    st.markdown("### ✨ 美颜滤镜")
    st.info("美颜滤镜开发中，敬请期待")

def render_gif_export():
    st.markdown("### 🎞️ 导出GIF")
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

# ========== 主程序 ==========
def main():
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    
    init_db()
    init_poster_tables()
    
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
    
    # 标题
    st.markdown("""
    <div class="main-header">
        <div style="font-size: 60px;">🤖</div>
        <h1>小智 - 智能视频助手</h1>
        <p>你的AI视频创作伙伴</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 上传区域
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
    
    # 板块1：视频创作工坊
    st.markdown('<div class="section-title">🎬 视频创作工坊</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
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
                start = st.number_input("开始(秒)", 0.0, dur, 0.0)
                end = st.number_input("结束(秒)", 0.0, dur, min(5.0, dur))
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                cut_video(st.session_state.video_path, start, end, out)
                with open(out, "rb") as f:
                    st.download_button("下载", f, file_name="cut.mp4")
            else:
                st.warning("请先上传视频")
    
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
                speed = st.number_input("倍数", 0.5, 2.0, 1.0)
                out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                speed_video(st.session_state.video_path, speed, out)
                with open(out, "rb") as f:
                    st.download_button("下载", f, file_name="speed.mp4")
            else:
                st.warning("请先上传视频")
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎞️</div>
            <div class="feature-name">导出GIF</div>
            <div class="feature-desc">制作动图表情</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("导出GIF", key="gif_btn"):
            render_gif_export()
    
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
    
    # 板块2：AI与生态
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
            <div class="feature-icon">💰</div>
            <div class="feature-name">积分系统</div>
            <div class="feature-desc">创作赚积分</div>
        </div>
        """, unsafe_allow_html=True)
        points = get_points(st.session_state.username)
        st.info(f"当前积分：{points}")
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-name">数据统计</div>
            <div class="feature-desc">成长看得见</div>
        </div>
        """, unsafe_allow_html=True)
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM posters WHERE creator = ?", (st.session_state.username,))
        poster_count = c.fetchone()[0]
        conn.close()
        st.metric("已发布版图", poster_count)

if __name__ == "__main__":
    main()
