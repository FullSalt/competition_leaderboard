import streamlit as st
import streamlit_authenticator as stauth
import extra_streamlit_components as stx
import yaml
from competition import app

st.set_page_config(page_title="Competition", layout="wide", initial_sidebar_state="collapsed")


# ログインの設定ファイルの読み込み
with open('config_login.yaml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
       
authenticator2 = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized'],
)

# ログインメソッドで入力フォームを配置
name, authentication_status2, username = authenticator2.login('Login', 'main')
print(name, authentication_status2, username)

if 'authentication_status2' not in st.session_state:
    st.session_state['authentication_status2'] = None

if st.session_state["authentication_status2"]:
    authenticator2.logout('Logout', 'main', key='logout2')
    st.write(f'ログインに成功しました')
		# ここにログイン後の処理を書く。
    app()
elif st.session_state["authentication_status2"] is False:
    st.error('ユーザ名またはパスワードが間違っています')
elif st.session_state["authentication_status2"] is None:
    st.warning('ユーザ名やパスワードを入力してください')
# 