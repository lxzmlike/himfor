import streamlit as st

st.set_page_config(page_title="小智", layout="wide")

st.title("小智 — 你的AI伙伴")
st.write("欢迎！请先注册或登录")

# 简单登录/注册界面（不用数据库，只做演示）
with st.sidebar:
    st.header("用户中心")
    choice = st.radio("", ["登录", "注册"])
    if choice == "登录":
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.button("登录"):
            st.success(f"欢迎回来，{username}")
    else:
        new_user = st.text_input("新用户名")
        new_pass = st.text_input("新密码", type="password")
        if st.button("注册"):
            st.success(f"注册成功！请登录")
