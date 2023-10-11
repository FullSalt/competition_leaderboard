import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import yaml
import datetime
import pytz
import json
import os
import shutil
import pygwalker as pyg
import streamlit.components.v1 as components

from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
# AUC
from sklearn.metrics import roc_auc_score



def app():
    # 日本時間の設定
    jst = pytz.timezone('Asia/Tokyo')

    flag_tier1 = False
    flag_submit = False

    # ワイドモードに設定
    # サイドバーをデフォルトでは閉じる
    

    # ログインの設定ファイルの読み込み
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )

    # 設定ファイルの読み込み
    df_info = pd.read_csv('info.csv', header=None, index_col=0).squeeze("columns")
    load_confing = json.load(open('config.json', 'r'))

    with st.sidebar:
        st.title('コンペティションの選択')
        competition_names = [item['competition_name'] for item in load_confing['competition']]
        index_default_comp = competition_names.index(df_info['competition_name'])
        selected_comp = st.selectbox('コンペティションを選択してください。', competition_names, index=index_default_comp)
        if st.button('保存', key='save_selected_comp'):
            df_info['competition_name'] = selected_comp
            df_info.to_csv('info.csv', header=False)
        st.write('---')

    # ランキングを読み込み

    index = next((i for i, item in enumerate(load_confing['competition']) if item['competition_name'] == selected_comp), None)

    if not "ranking.csv" in os.listdir(f"competition/{load_confing['competition'][index]['competition_dir']}"):
        ranking_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/ranking.csv"
        ranking_df = pd.DataFrame(columns=['Name', 'Group', 'Accuracy', 'Recall', 'Precision', 'F1-score', 'AUC', 'Comment', 'Submitted Time'])
        ranking_df.to_csv(ranking_file_patn, index=False) 
        print('ランキングファイルを作成しました。')
    else:
        ranking_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/ranking.csv"
        ranking_df = pd.read_csv(ranking_file_patn)

    answercsv_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/submission_answer.csv"
    traincsv_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/{load_confing['competition'][index]['train_csv']}"
    testcsv_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/{load_confing['competition'][index]['test_csv']}"

    flag_filtered = df_info['group_filter']

    # サイドバーの評価指標の設定
    with st.sidebar:
        st.title('評価指標')
        option = ['Accuracy', 'Recall', 'Precision', 'F1-score', 'AUC']
        index_default = option.index(df_info['score'])
        selected_score = st.selectbox('評価指標を選択してください。', option, index=index_default)
        if st.button('保存', key='save_selected_score'):
            df_info['score'] = selected_score
            df_info.to_csv('info.csv', header=False)
        st.write('---')

    with st.sidebar:
        st.title('コメント参照')
        # インデックスを入力して、コメントを見る
        if len(ranking_df) > 0:
            comment_num = st.number_input('コメントを見るインデックスを入力', min_value=0, max_value=len(ranking_df)-1, value=0)
            st.text(ranking_df['Comment'][comment_num])
        st.write('---')

        # グループ名検索
        st.title('グループ名で検索')
        search_group_name = st.text_input('グループ名を入力してください。', key='input_group_name2search')
        if st.button('完全一致', key='search_group_name'):
            flag_filtered = 'exact'
            df_info['group_filter'] = 'exact'
            df_info.to_csv('info.csv', header=False)
        if st.button('部分一致', key='search_group_name_partial'):
            flag_filtered = 'partial'
            df_info['group_filter'] = 'partial'
            df_info.to_csv('info.csv', header=False)
        if st.button('リセット', key='reset_group_name'):
            flag_filtered = 'none'
            df_info['group_filter'] = 'none'
            df_info.to_csv('info.csv', header=False)
        # st.write(df_info)
        st.write('---') 

    # 指定した評価指標でソート
    ranking_df = ranking_df.sort_values(selected_score, ascending=False)
    # ランクを付与
    rank = ranking_df[selected_score].rank(method='min', ascending=False).astype(int)
    ranking_df.insert(0, 'Rank', rank)
    # ランクでソート
    ranking_df = ranking_df.sort_values('Rank', ascending=True)
    # インデックスを振り直す
    ranking_df = ranking_df.reset_index(drop=True)

    # 管理者用のサイドバー
    with st.sidebar:

        st.title('管理者用')

        # ログインメソッドで入力フォームを配置
        name, authentication_status, username = authenticator.login('Login', 'sidebar')
        # print(name, authentication_status, username)
        # 返り値、authenticaton_statusの状態で処理を場合分け
        if authentication_status:
            # logoutメソッドでaurhenciationの値をNoneにする
            authenticator.logout('Logout', 'sidebar', key='unique_key')
            st.button('管理者ページの内容の更新を反映', key='update')
            st.write(f'{name}関係者用の編集ページです。')
            # st.title('Some content')
            
            st.write('---')
            st.markdown('## コンペティションの追加')

            # competition の名前を設定
            _competition_name = st.text_input('コンペ名を入力してください。')

            # 答えのcsvファイルをアップロード
            _uploaded_input_file = st.file_uploader("答えの CSV ファイルをアップロードしてください。", type="csv", key='file_uploader2')
            if _uploaded_input_file is not None:
                add_test = pd.read_csv(_uploaded_input_file)
            _target_name = st.text_input('目的変数のカラム名を入力してください。')
            
            if st.button('コンペティション情報の保存', key='save_target_name'):
                if _competition_name == '':
                    st.write('Error：コンペティション名を入力してください。')
                elif _competition_name in competition_names:
                    st.write('Error：同じコンペティションが既に存在しています。')
                elif _uploaded_input_file is None:
                    st.write('Error：答えの CSV ファイルをアップロードしてください。')
                elif not _target_name in add_test.columns:
                    st.write('Error：csv ファイルの中にそのカラム名が含まれていません。')
                else:   
                    # ディレクトリを作成
                    os.mkdir(f'competition/{_competition_name}')

                    add_answercsv_file_patn = f"competition/{_competition_name}/submission_answer.csv"
                    add_test.to_csv(add_answercsv_file_patn, index=False)

                    load_confing['competition'].append({'competition_name': _competition_name, 'competition_dir': _competition_name.lower().replace(" ", ""), 'competition_target': _target_name})
                    with open('config.json', 'w') as f:
                        json.dump(load_confing, f, indent=4)
                    index = next((i for i, item in enumerate(load_confing['competition']) if item['competition_name'] == _competition_name), None)
                    answercsv_file_patn = f"competition/{_competition_name.lower().replace(' ', '')}/submission_answer.csv"
                    st.write('コンペティション情報を保存しました。')

            st.write('---')
            st.markdown('## コンペティションの削除')
            if len([item['competition_name'] for item in load_confing['competition']]) < 4:
                _competition_names = ['選択してください']
            else:
                _competition_names = ['選択してください'] + [item['competition_name'] for item in load_confing['competition']][3:]

            _selected_comp = st.selectbox('コンペティションを選択してください。', _competition_names, key='deletecomplist')
            if st.button('消去', key='delete_comp') and _selected_comp != '選択してください':
                _index = next((i for i, item in enumerate(load_confing['competition']) if item['competition_name'] == _selected_comp), None)

                # ディレクトリを削除
                shutil.rmtree(f"competition/{load_confing['competition'][_index]['competition_dir']}")
                # config.json から削除
                load_confing['competition'].pop(_index)
                with open('config.json', 'w') as f:
                    json.dump(load_confing, f, indent=4)
                df_info.to_csv('info.csv', header=False)
                # コンペティション名を再設定
                index = 0
                df_info['competition_name'] = load_confing['competition'][index]['competition_name']
                answercsv_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/submission_answer.csv"
                ranking_file_patn = f"competition/{load_confing['competition'][index]['competition_dir']}/ranking.csv"

                df_info['competition_name'] = load_confing['competition'][index]['competition_name']
                df_info.to_csv('info.csv', header=False)
        
            st.write('---') 
            st.markdown('## ランキングを出力')
            # 現在のランキングをcsvファイルで出力
            st.download_button('ランキングを CSV ファイルで出力', ranking_df.iloc[:,1:].to_csv(index=False), ranking_file_patn)
            
            st.markdown('## 過去のランキングを反映')
            # 過去のランキングを反映
            _uploaded_ranking_file = st.file_uploader("過去のランキングをアップロードしてください。", type="csv", key='file_uploader3')
            if st.button('ランキングを反映', key='reflect_ranking') and _uploaded_ranking_file is not None:
                _ranking_df = pd.read_csv(_uploaded_ranking_file)
                if ranking_df.columns.drop('Rank').tolist() == _ranking_df.columns.tolist():
                    ranking_df = _ranking_df
                    ranking_df.to_csv(ranking_file_patn, index=False)

                    # 指定した評価指標でソート
                    ranking_df = ranking_df.sort_values(selected_score, ascending=False)
                    # ランクを付与
                    rank = ranking_df[selected_score].rank(method='min', ascending=False).astype(int)
                    ranking_df.insert(0, 'Rank', rank)
                    # ランクでソート
                    ranking_df = ranking_df.sort_values('Rank', ascending=True)
                    # インデックスを振り直す
                    ranking_df = ranking_df.reset_index(drop=True)
                    st.write('ランキングを反映しました。')
                else:
                    st.write('Error：カラム名が一致しません。')

            st.write('---')
            st.markdown('## ランキングの編集')
            st.write(ranking_df.iloc[:,1:])
            # 消去するインデックスを入力
            if len(ranking_df) > 0:
                cleared_num = st.number_input('消去するインデックスを入力', min_value=0, max_value=len(ranking_df)-1)
            if st.button('消去', key="deleteindex") and len(ranking_df) > 0:
                ranking_df = pd.read_csv(ranking_file_patn)
                ranking_df = ranking_df.drop(index=cleared_num)
                ranking_df.to_csv(ranking_file_patn, index=False)

                # 指定した評価指標でソート
                ranking_df = ranking_df.sort_values(selected_score, ascending=False)
                # ランクを付与
                rank = ranking_df[selected_score].rank(method='min', ascending=False).astype(int)
                ranking_df.insert(0, 'Rank', rank)
                # ランクでソート
                ranking_df = ranking_df.sort_values('Rank', ascending=True)
                # インデックスを振り直す
                ranking_df = ranking_df.reset_index(drop=True)
            # st.write(ranking_df.iloc[:3, :3])

            # ランキングをリセット 
            if st.button('ランキングをリセット', key='reset_ranking'):
                ranking_df = pd.DataFrame(columns=['Name', 'Group', 'Accuracy', 'Recall', 'Precision', 'F1-score', 'AUC', 'Comment', 'Submitted Time'])
                ranking_df.to_csv(ranking_file_patn, index=False) 

        elif authentication_status == False:
            st.error('Username/password is incorrect')
        # elif authentication_status == None:
        #     st.warning('Please enter your username and password')

    # ---------------------------------------------------------------------------------

    # タイトルを表示
    st.title(selected_comp)
    st.write('---')

    st.markdown('## コンペティションの説明')
    st.write(f"""
            下記のtrain.csv をクリックしてダウンロードできるデータから、{load_confing['competition'][index]['competition_target']} を予測する分類モデルを作成して、
            その学習済みモデルから下記のtest.csv をクリックしてダウンロードできるデータに対して予測値を計算し、CSVファイルとして提出してください。""")

    st.write('学習に使用するデータ')
    df_train = pd.read_csv(traincsv_file_patn)
    st.download_button('train.csv',data=pd.read_csv(traincsv_file_patn).to_csv(index=False) ,file_name=os.path.basename(traincsv_file_patn))

    st.write('正解のない評価用のデータ')
    st.download_button('test.csv',data=pd.read_csv(testcsv_file_patn).to_csv(index=False) ,file_name=os.path.basename(testcsv_file_patn))

    st.write('---')
    st.markdown('## PyGWalker でデータの可視化')
    pyg_html=pyg.walk(df_train, evn='Streamlit', return_html=True)
    components.html(pyg_html, height=900, scrolling=True)

    st.write('---')
    st.markdown('## スコアを提出しよう！')

    # 答えの csv ファイルを読み込み
    df_answer = pd.read_csv(answercsv_file_patn)
    series_ans = df_answer[load_confing['competition'][index]['competition_target']]

    # 名前とグループを入力
    challenger_name = st.text_input('本名ではなくニックネームを入力してください。(必須)')
    group_name = st.text_input('グループ名を入力してください。')
    comment_text = st.text_area('行なった工夫やコメントを入力してください。')

    # streamlitでファイルをアップロード
    uploaded_file = st.file_uploader(f"CSV ファイルをアップロードしてください。(必須)\n予測値のカラム名は、「{load_confing['competition'][index]['competition_target']}」にしてください。", type="csv", key='file_uploader1')
    if uploaded_file is not None:
        df_submission = pd.read_csv(uploaded_file)
        series_submission = df_submission[load_confing['competition'][index]['competition_target']]

    # 評価ボタンが押されたら
    if st.button('評価', key='submit'):
        if challenger_name == '':
            st.warning('ニックネームを入力してください。')
        elif uploaded_file is None:
            st.warning('CSVファイルをアップロードしてください。')
        # 提出された CSV ファイルの行数が足りない場合
        elif len(series_ans) != len(series_submission):
            st.warning('提出された CSV ファイルの行数が足りません。  \n\
                    欠損値のある行を削除してしまっている可能性があります。')
        
        # 評価指標を計算
        elif challenger_name != '' and uploaded_file is not None:

            # 評価指標を計算
            score_acc = accuracy_score(series_ans, series_submission)*100
            score_rec = recall_score(series_ans, series_submission)*100
            score_pre = precision_score(series_ans, series_submission)*100
            score_f1 = f1_score(series_ans, series_submission)*100
            score_auc = roc_auc_score(series_ans, series_submission)*100

            submitted_time = datetime.datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')

            # st.write('Accuracy：', score_acc, '%')
            # st.write('Recall：', score_rec, '%')
            # st.write('Precision：', score_pre, '%')
            # st.write('F1score：', score_f1, '%')
            # st.write('AUC：', score_auc, '%')

            # 識別用の名前とグループと評価指標ををDataFrameに格納
            df_score = pd.DataFrame({'Name': [challenger_name],
                                    'Group': [group_name],
                                    'Accuracy': [score_acc],
                                    'Recall': [score_rec],
                                    'Precision': [score_pre],
                                    'F1-score': [score_f1],
                                    'AUC': [score_auc],
                                    'Comment': [comment_text],
                                    'Submitted Time': [submitted_time]})
            
            # ranking_df に df_score と同じ行がなければ追加
            if ranking_df[ranking_df['Name'] == challenger_name].empty:
                ranking_df = pd.concat([ranking_df, df_score], axis=0)
                # Rnak 列を削除
                ranking_df = ranking_df.drop(columns=['Rank'])

                # 指定した評価指標でソート
                ranking_df = ranking_df.sort_values(selected_score, ascending=False)
                # スコアを保存
                ranking_df.to_csv(ranking_file_patn, index=False)

                # ランクを付与
                rank = ranking_df[selected_score].rank(method='min', ascending=False).astype(int)
                ranking_df.insert(0, 'Rank', rank)
                # ランクでソート
                ranking_df = ranking_df.sort_values('Rank', ascending=True)
                # インデックスを振り直す
                ranking_df = ranking_df.reset_index(drop=True)
            else:
                st.warning('すでに登録されています。')

            flag_tier1 = True
            flag_submit = True

    # ---------------------------------------------------------------------------------


    st.write('---')

    # アップロードしたデータがランキング1位だったら
    if len(ranking_df) > 0 and flag_tier1:
        if ranking_df[ranking_df['Name'] == challenger_name]['Rank'].values[0]==1:
            st.title(f'{challenger_name}、あなたがNo.1だ！')
            st.balloons()
            flag_tier1 = False

    # アップロードされたデータを表示
    if len(ranking_df) > 0 and flag_submit:
        st.markdown('## あなたが提出したスコア！')
        st.write(ranking_df[ranking_df['Name'] == challenger_name].to_html(index=True, index_names=True), unsafe_allow_html=True)   
        flag_submit = False

    #Rank 列を削除して保存
    if 'Rank' in ranking_df.columns:
        ranking_df.drop(labels=['Rank'], axis=1).to_csv(ranking_file_patn, index=False)

    st.markdown('## Leaderboard')
    st.markdown(f'### 評価指標：{selected_score}が高い順で表示')

    # Group名でフィルタリングされたら
    if flag_filtered == 'partial':
        ranking_df = ranking_df[ranking_df['Group'].str.contains(search_group_name, na=False)]
        st.markdown(f'### グループ名が {search_group_name} に部分一致')
    elif flag_filtered == 'exact':
        ranking_df = ranking_df[ranking_df['Group'] == search_group_name]
        st.markdown(f'### グループ名が {search_group_name} に完全一致')

    float_columns = ranking_df.select_dtypes(include=['float64']).columns
    ranking_df[float_columns] = ranking_df[float_columns].apply(lambda col: col.map("{:.2f}".format))

    ranking_df['Comment'] = ranking_df['Comment'].fillna('')
    ranking_df['Submitted Time'] = ranking_df['Submitted Time'].fillna('')
    ranking_df['Comment'] = ranking_df['Comment'].apply(lambda x: x.split('\n')[0])
    # DataFrameをHTMLに変換し、インデックスを表示する
    df_html = ranking_df.to_html(index=True, index_names=True)

    # HTMLを表示
    st.write(df_html, unsafe_allow_html=True)

    st.write('---')