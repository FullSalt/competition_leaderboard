import streamlit as st
import pandas as pd
import sqlite3 
import hashlib
from competition import app

st.set_page_config(page_title="Competition", layout="wide", initial_sidebar_state="collapsed")

conn = sqlite3.connect('database.db')
c = conn.cursor()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def create_user():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')

def add_user(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data

def main():

    st.title("キカガク コンペティション！")

    # セッションステートを取得
    if 'loggedin' not in st.session_state:
        st.session_state.loggedin = False
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""

    if not st.session_state.loggedin:
        st.subheader("ログイン画面です")

        user_name = st.text_input("ユーザー名を入力してください")
        password = st.text_input("パスワードを入力してください", type='password')

        if st.button("ログイン"):
            create_user()  # この関数の内容が不明なので、適切に機能するか確認してください
            hashed_pswd = make_hashes(password)

            result = login_user(user_name, check_hashes(password, hashed_pswd))
            if result:
                st.success("{}さんでログインしました".format(user_name))
                st.session_state.loggedin = True
                st.session_state.user_name = user_name
                app()
            else:
                st.warning("ユーザー名かパスワードが間違っています")
    else:
        st.success("{}さんでログイン中".format(st.session_state.user_name))
        app()
if __name__ == '__main__':
	main()