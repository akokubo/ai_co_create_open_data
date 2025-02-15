import streamlit as st
import pandas as pd
import os
import ollama

# --- オープンデータの読み込み ---
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
                df = pd.read_csv(file_path, encoding="cp932") # Shift_JISに対応
                data_content = df.head().to_dict() # 転置して辞書型に変換
            elif data_type == "excel":
                df = pd.read_excel(file_path)
                data_content = df.head().to_dict() # 転置して辞書型に変換
            elif data_type == "md":
                with open(file_path, "r", encoding="utf-8") as f:
                    data_content = f.read()
            else:
                data_content = f"不明なデータ形式: {data_type}"
        except Exception as e:
            data_content = f"エラー: {str(e)}"
        
        data_dict[data_name] = data_content
    return data_dict

open_data = load_open_data()

# --- Streamlit画面レイアウト ---
st.set_page_config(page_title="八戸のオープンデータを×(かけ)て生成AIに聞いてみよう！", layout="wide")
st.markdown(
    "<h1>生成AIで「<span style='font-size: xxx-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸オープンデータ</h1>", 
    unsafe_allow_html=True
)

st.markdown(
    "「<span style='font-size: x-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸のオープンデータを左で選んで生成AIに質問してみよう！", 
    unsafe_allow_html=True
)

# サイドバー：使用するオープンデータの選択
st.sidebar.image("images/ai_co_create_open_data_hachinohe.png", width=200)
st.sidebar.title("使用するオープンデータ")
selected_data_names = [
    name for name in open_data.keys() if st.sidebar.checkbox(name)
]

# ユーザーの質問入力
user_question = st.text_area("質問を入力してください", height=150)

# --- プロンプトの生成 ---
def generate_prompt(selected_data, question):
    """プロンプトを生成する関数"""
    prompt_lines = [
        "'''",
        "# 使用するオープンデータ"
    ]
    for name, content in selected_data.items():
        prompt_lines.append(f"{name} = {content}")
    
    prompt_lines.extend([
        "----",
        "# あなたの役割",
        "あなたは、経験豊富で思慮深くアイデアに満ちたアドバイザーです。",
        "# 依頼",
        "以上は、八戸市のオープンデータです。",
        question,
        "段階的に考えて、回答する前に回答を見直しして改善してから、回答してください。",
        "'''"
    ])
    return "\n".join(prompt_lines)

# --- ボタン押下時の処理 ---
if st.button("生成AIに聞いてみる") and user_question:
    if not selected_data_names:
        st.warning("オープンデータを1つ以上選択してください。")
    else:
        # 選択されたオープンデータのみプロンプトに含める
        selected_data = {name: open_data[name] for name in selected_data_names}
        prompt = generate_prompt(selected_data, user_question)
        
        # プロンプトの内容を表示（デバッグ用）
        # st.text_area("生成されたプロンプト", prompt, height=300)
        
        # --- LLM（Ollama）の呼び出し ---
        MODEL = "hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest"
        stream = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
        )
        
        # LLMのレスポンスを表示
        response_buffer = ''
        response_placeholder = st.empty()
        for chunk in stream:
            response_buffer += chunk['message']['content']
            response_placeholder.markdown(response_buffer)
