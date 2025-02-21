MODEL = 'hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest'
BASE_URL = 'http://localhost:11434/v1'
OPENAI_API_KEY = 'ollama'

import os
import streamlit as st
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.callbacks.base import BaseCallbackHandler

# ストリーミング用のコールバックハンドラ
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.full_response = ""
    def on_llm_new_token(self, token: str, **kwargs):
        self.full_response += token
        self.placeholder.markdown(self.full_response)

# Excelからオープンデータを読み込む関数
@st.cache_data(show_spinner=False)
def load_open_data():
    opendata_df = pd.read_excel("data/opendata.xlsx")
    data_dict = {}
    for _, row in opendata_df.iterrows():
        data_name = row["データ名"]
        data_type = str(row["データの種類"]).lower().strip()
        file_name = row["ファイル名"]
        file_path = os.path.join(os.getcwd(), str(file_name))
        try:
            if data_type == "csv":
                df = pd.read_csv(file_path, encoding="cp932")
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

# ユーザー入力と選択したオープンデータから、LangChain形式のプロンプトメッセージを作成
def build_prompt(user_input, selected_data):
    lines = ["# 使用するオープンデータ"]
    for name, content in selected_data.items():
        lines.append(f"{name} = {content}")
    lines.append("----")
    lines.append("以上は、八戸市のオープンデータです。")
    lines.append("")
    lines.append("# 依頼")
    lines.append(user_input)
    lines.append("")
    lines.append("# 依頼")
    lines.append("ステップバイステップで考えて、回答してください。")
    lines.append("回答する前に回答を見直しして改善してから、回答してください。")
    
    human_message = "\n".join(lines)
    
    messages = [
        SystemMessage(content="あなたは、経験豊富で思慮深くアイデアに満ちた親切なアドバイザーです。"),
        HumanMessage(content=human_message)
    ]
    return messages

def main():
    st.set_page_config(
        page_title="八戸のオープンデータを×(かけ)て生成AIに聞いてみよう！",
        page_icon="🐈‍⬛",
        layout="wide"
    )

    st.markdown(
        "<h1>生成AIで「<span style='font-size: xxx-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸オープンデータ</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "「<span style='font-size: x-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸のオープンデータを左で選んで生成AIに質問してみよう！", 
        unsafe_allow_html=True
    )
    
    # サイドバーでオープンデータの選択
    st.sidebar.image("images/ai_co_create_open_data_hachinohe.png", width=200)
    st.sidebar.title("使用するオープンデータ")
    
    open_data = load_open_data()
    selected_data_names = [name for name in open_data.keys() if st.sidebar.checkbox(name)]
    if not selected_data_names:
        st.warning("左側でオープンデータを1つ以上選択してください。")
        st.stop()
    selected_data = {name: open_data[name] for name in selected_data_names}
    
    # セッション状態の初期化
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # フォームのキー用のカウンター（新規キーでウィジェットを再生成）
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    # チャット履歴の表示
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn["assistant"])
            
    st.markdown("---")
    
    # ユニークなキーでフォームを作成
    form_key = f"chat_form_{st.session_state.form_key}"
    input_key = f"input_text_{st.session_state.form_key}"
    with st.form(key=form_key):
        user_input = st.text_input("質問を入力してください", key=input_key, value="")
        submit_button = st.form_submit_button("AIに聞いてみる")
    
    if submit_button and user_input:
        st.session_state.chat_history.append({"user": user_input, "assistant": ""})
        messages = build_prompt(user_input, selected_data)
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            with st.spinner("生成AIが回答を生成しています..."):
                try:
                    callback_handler = StreamlitCallbackHandler(response_placeholder)
                    chat_model = ChatOpenAI(
                        model_name=MODEL,
                        streaming=True,
                        callbacks=[callback_handler],
                        temperature=0,
                        base_url=BASE_URL,
                        openai_api_key=OPENAI_API_KEY,
                    )
                    response = chat_model(messages)
                    assistant_response = response.content
                    st.session_state.chat_history[-1]["assistant"] = assistant_response
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
        # 送信後、form_key をインクリメントすることで次回は新しいキーでフォームを生成
        st.session_state.form_key += 1
        st.rerun()

if __name__ == "__main__":
    main()
