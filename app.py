MODEL = 'hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest'
BASE_URL = 'http://localhost:11434/v1'
API_KEY = 'ollama'

import streamlit as st
import pandas as pd
import os
from openai import OpenAI

st.set_page_config(
    page_title="八戸のオープンデータを×(かけ)て生成AIに聞いてみよう！", 
    layout="wide"
)

# OpenAIクライアントの初期化
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,  # 必須項目（未使用）
)

@st.cache_data(show_spinner=False)
def load_open_data():
    """オープンデータを読み込む関数"""
    opendata_df = pd.read_excel("data/opendata.xlsx")
    data_dict = {}
    
    for _, row in opendata_df.iterrows():
        data_name = row["データ名"]
        data_type = str(row["データの種類"]).lower().strip()
        file_name = row["ファイル名"]
        file_path = os.path.join(os.getcwd(), str(file_name))
        
        try:
            if data_type == "csv":
                df = pd.read_csv(file_path, encoding="cp932")  # Shift_JISに対応
                data_content = df.head().to_dict()
            elif data_type == "excel":
                df = pd.read_excel(file_path)
                data_content = df.head().to_dict()
            elif data_type == "md":
                with open(file_path, "r", encoding="utf-8") as f:
                    data_content = f.read()
            else:
                data_content = f"不明なデータ形式: {data_type}"
        except Exception as e:
            data_content = f"エラー: {str(e)}"
        
        data_dict[data_name] = data_content
    return data_dict

def generate_system_message(selected_data, show_content=True):
    """
    システムメッセージを生成する関数
    show_content=True の場合はオープンデータの内容を含む（API送信用）
    show_content=False の場合は、内容部分を【非表示】に置き換える（UI表示用）
    """
    prompt_lines = [
        "'''",
        "# 使用するオープンデータ"
    ]
    for name, content in selected_data.items():
        if show_content:
            prompt_lines.append(f"{name} = {content}")
        else:
            prompt_lines.append(f"{name} = 【非表示】")
    prompt_lines.extend([
        "----",
        "以上は、八戸市のオープンデータです。",
        "# あなたの役割",
        "あなたは、経験豊富で思慮深くアイデアに満ちたアドバイザーです。",
        "# 依頼",
        "ステップバイステップで考えて、回答してください。",
        "回答する前に回答を見直しして改善してから、回答してください。",
        "'''"
    ])
    return "\n".join(prompt_lines)

def get_display_prompt(chat_history, selected_data):
    """
    APIに送信した会話コンテキストを、システムメッセージ部分のみオープンデータ内容を非表示にした形で
    連結して表示用の文字列を生成する
    """
    display_text = ""
    for message in chat_history:
        if message["role"] == "system":
            content = generate_system_message(selected_data, show_content=False)
            role_label = "システム"
        elif message["role"] == "user":
            content = message["content"]
            role_label = "あなた"
        else:
            content = message["content"]
            role_label = "アシスタント"
        display_text += f"**{role_label}:**\n{content}\n\n"
    return display_text

def main():
    # オープンデータの読み込み
    open_data = load_open_data()
    
    st.markdown(
        "<h1>生成AIで「<span style='font-size: xxx-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸オープンデータ</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "「<span style='font-size: x-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸のオープンデータを左で選んで生成AIに質問してみよう！", 
        unsafe_allow_html=True
    )
    
    # サイドバー：オープンデータの選択
    st.sidebar.image("images/ai_co_create_open_data_hachinohe.png", width=200)
    st.sidebar.title("使用するオープンデータ")
    selected_data_names = [
        name for name in open_data.keys() if st.sidebar.checkbox(name)
    ]
    
    # オープンデータが未選択の場合は処理を中断
    if not selected_data_names:
        st.warning("左側でオープンデータを1つ以上選択してください。")
        st.stop()
    
    # 選択されたオープンデータのみを使用
    selected_data = {name: open_data[name] for name in selected_data_names}
    
    # セッション状態で会話履歴を管理（オープンデータ選択が変わった場合はリセット）
    if "session_selected_data_names" not in st.session_state:
        st.session_state.session_selected_data_names = selected_data_names
        st.session_state.chat_history = []
    elif st.session_state.session_selected_data_names != selected_data_names:
        st.session_state.session_selected_data_names = selected_data_names
        st.session_state.chat_history = []
        
    # ユーザー入力ウィジェット用のカウンター（入力欄のキーを動的に変更するため）
    if "user_input_counter" not in st.session_state:
        st.session_state.user_input_counter = 0

    # 初回の会話の場合、システムメッセージ（API送信用）を会話履歴に追加
    if not st.session_state.chat_history:
        system_message = generate_system_message(selected_data, show_content=True)
        st.session_state.chat_history.append({"role": "system", "content": system_message})
    
    # チャット履歴の表示（システムメッセージは表示しない）
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
    
    st.markdown("---")
    
    # 下部に質問入力欄を配置（フォーム）
    with st.form("chat_form", clear_on_submit=False):
        input_key = f"user_input_{st.session_state.user_input_counter}"
        user_input = st.text_input("質問を入力してください", key=input_key)
        submitted = st.form_submit_button("AIに聞いてみる")
        if submitted and user_input:
            # ユーザーの入力をチャット履歴に追加してすぐ表示
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                with st.spinner("生成AIが回答を生成しています..."):
                    try:
                        # OpenAI Chat API の呼び出し（ストリーミング対応）
                        response = client.chat.completions.create(
                            model=MODEL,
                            messages=st.session_state.chat_history,
                            stream=True,
                        )
                        
                        assistant_response = ""
                        for chunk in response:
                            # 各チャンクの内容は choices[0].delta 経由で取得
                            delta = chunk.choices[0].delta.content
                            assistant_response += delta
                            response_placeholder.markdown(assistant_response)
                        
                        # 完成したアシスタントの回答をチャット履歴に追加
                        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    except Exception as e:
                        st.error(f"API呼び出し中にエラーが発生しました: {str(e)}")
            
            # 入力欄は新たなキーで再生成されるので自動的に空欄になります
            st.session_state.user_input_counter += 1
            st.rerun()
    
    # 生成されたプロンプト（会話コンテキスト）の確認用Expander（オープンデータ内容は【非表示】）
    with st.expander("生成されたプロンプトを見る"):
        prompt_display = get_display_prompt(st.session_state.chat_history, selected_data)
        st.code(prompt_display, language="markdown")

if __name__ == "__main__":
    main()
