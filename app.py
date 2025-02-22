MODEL = "hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest"
BASE_URL = "http://localhost:11434/v1"
OPENAI_API_KEY = "ollama" # 指定はするが、実際には使用しない

import os
import pandas as pd

# LangChain関連のモジュール（チャットモデル、メッセージ形式、コールバックハンドラ）
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.callbacks.base import BaseCallbackHandler

import streamlit as st
import warnings
# Streamlitでヘッダーとフッターが解析できない警告を無視
warnings.filterwarnings("ignore", message="Cannot parse header or footer so it will be ignored")

# -----------------------------------------------------------------------------
# ストリーミング用のコールバックハンドラ
# LangChainから新しいトークンが生成されるたびに呼び出され、
# Streamlitのプレースホルダーにリアルタイムで表示を更新するためのクラス
# -----------------------------------------------------------------------------
class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, placeholder):
        # Streamlitの表示用プレースホルダーを保持
        self.placeholder = placeholder
        # 生成されたトークンを連結して保持する変数
        self.full_response = ""
    
    def on_llm_new_token(self, token: str, **kwargs):
        # 新たなトークンを受け取るたびにfull_responseに追加
        self.full_response += token
        # 現在までの全体レスポンスをMarkdown形式で表示更新
        self.placeholder.markdown(self.full_response)

# -----------------------------------------------------------------------------
# Excelからオープンデータを読み込む関数
# Streamlitのキャッシュ機能を利用して、読み込みを効率化
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_open_data():
    # "data/opendata.xlsx"からデータを読み込み
    opendata_df = pd.read_excel("data/opendata.xlsx")
    data_dict = {}
    # Excelファイルの各行を処理
    for _, row in opendata_df.iterrows():
        # データ名、データの種類、ファイル名を取得
        data_name = row["データ名"]
        data_type = str(row["データの種類"]).lower().strip()  # 小文字に変換し、前後の空白を削除
        file_name = row["ファイル名"]
        # カレントディレクトリとファイル名を結合して、ファイルパスを生成
        file_path = os.path.join(os.getcwd(), str(file_name))
        try:
            # CSV形式の場合：cp932エンコーディングで読み込み、先頭部分を辞書に変換
            if data_type == "csv":
                df = pd.read_csv(file_path, encoding="cp932")
                data_content = df.head().to_dict()
            # Excel形式の場合：先頭部分を辞書に変換
            elif data_type == "excel":
                df = pd.read_excel(file_path)
                data_content = df.head().to_dict()
            # Markdown形式の場合：ファイル内容をそのままテキストとして読み込み
            elif data_type == "md":
                with open(file_path, "r", encoding="utf-8") as f:
                    data_content = f.read()
            # 上記以外の場合は不明なデータ形式として扱う
            else:
                data_content = f"不明なデータ形式: {data_type}"
        except Exception as e:
            # 読み込み中にエラーが発生した場合は、エラーメッセージを設定
            data_content = f"エラー: {str(e)}"
        # 辞書にデータ名をキーとして格納
        data_dict[data_name] = data_content
    return data_dict

# -----------------------------------------------------------------------------
# ユーザー入力と選択したオープンデータから、LangChain形式のプロンプトメッセージを作成する関数
# -----------------------------------------------------------------------------
def build_prompt(user_input, selected_data):
    lines = ["# 使用するオープンデータ"]
    # 選択されたオープンデータの名前と内容をテキスト形式で追加
    for name, content in selected_data.items():
        lines.append(f"{name} = {content}")
    lines.append("----")
    lines.append("以上は、八戸市のオープンデータです。")
    lines.append("")
    lines.append("# ユーザーの質問")
    # ユーザーからの質問を追加
    lines.append(user_input)
    lines.append("")
    lines.append("# 依頼")
    # 生成AIへの具体的な指示（ステップバイステップで考えて回答するよう依頼）
    lines.append("ユーザーの質問にステップバイステップで考えて、回答してください。")
    lines.append("回答する前に回答を見直しして改善してから、回答してください。")
    
    # リスト化された行を1つのテキストに結合
    human_message = "\n".join(lines)
    
    # LangChainのメッセージ形式に変換
    messages = [
        SystemMessage(content="あなたは、経験豊富で思慮深くアイデアに満ちた親切なアドバイザーです。"),
        HumanMessage(content=human_message)
    ]
    return messages

# -----------------------------------------------------------------------------
# Streamlitアプリのメイン処理
# -----------------------------------------------------------------------------
def main():
    # ページの基本設定（タイトル、アイコン、レイアウトなど）
    st.set_page_config(
        page_title="八戸のオープンデータを×(かけ)て生成AIに聞いてみよう！",
        page_icon="🐈‍⬛",
        layout="wide"
    )

    # ページのヘッダー部分のHTMLマークアップ（タイトルの表示）
    st.markdown(
        "<h1>生成AIで「<span style='font-size: xxx-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸オープンデータ</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "「<span style='font-size: x-large;'><ruby>×<rp>(</rp><rt>カケ</rt><rp>)</rp></ruby>る</span>」八戸のオープンデータを左で選んで生成AIに質問してみよう！", 
        unsafe_allow_html=True
    )
    
    # -----------------------------------------------------------------------------
    # サイドバーの設定：画像表示とオープンデータの選択
    # -----------------------------------------------------------------------------
    st.sidebar.image("images/ai_co_create_open_data_hachinohe.png", use_container_width=True)
    st.sidebar.title("使用するオープンデータ")
    
    # Excelからオープンデータを読み込む
    open_data = load_open_data()
    # 各オープンデータに対してチェックボックスを作成し、選択されたデータ名のリストを生成
    selected_data_names = [name for name in open_data.keys() if st.sidebar.checkbox(name)]
    # もし1つも選択されなかった場合は、警告を表示して処理を中断
    if not selected_data_names:
        st.warning("左側でオープンデータを1つ以上選択してください。")
        st.stop()
    # 選択されたデータのみを辞書にまとめる
    selected_data = {name: open_data[name] for name in selected_data_names}
    
    # -----------------------------------------------------------------------------
    # セッション状態の初期化（チャット履歴とフォーム用のキー）
    # -----------------------------------------------------------------------------
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # 新しいフォームウィジェットを生成するためのキー
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    # -----------------------------------------------------------------------------
    # これまでのチャット履歴を表示
    # -----------------------------------------------------------------------------
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn["assistant"])
            
    st.markdown("---")
    
    # -----------------------------------------------------------------------------
    # ユニークなキーでフォームを作成（ユーザーの質問入力フォーム）
    # -----------------------------------------------------------------------------
    form_key = f"chat_form_{st.session_state.form_key}"
    input_key = f"input_text_{st.session_state.form_key}"
    with st.form(key=form_key):
        # テキスト入力ウィジェットでユーザーの質問を受け付ける
        user_input = st.text_input("質問を入力してください", key=input_key, value="")
        # フォーム送信ボタン
        submit_button = st.form_submit_button("AIに聞いてみる")
    
    # -----------------------------------------------------------------------------
    # ユーザーからの入力があった場合の処理
    # -----------------------------------------------------------------------------
    if submit_button and user_input:
        # ユーザーの入力をチャット履歴に追加（アシスタントの回答は初めは空）
        st.session_state.chat_history.append({"user": user_input, "assistant": ""})
        # ユーザーの入力と選択されたオープンデータからプロンプトメッセージを作成
        messages = build_prompt(user_input, selected_data)
        
        with st.chat_message("assistant"):
            # アシスタントの回答表示用のプレースホルダーを作成
            response_placeholder = st.empty()
            # 応答生成中にスピナーを表示
            with st.spinner("生成AIが回答を生成しています..."):
                try:
                    # ストリーミング用のコールバックハンドラを初期化
                    callback_handler = StreamlitCallbackHandler(response_placeholder)
                    # ChatOpenAIモデルのインスタンスを作成し、ストリーミング、温度、APIキーなどを指定
                    chat_model = ChatOpenAI(
                        model_name=MODEL,
                        streaming=True,
                        callbacks=[callback_handler],
                        temperature=0.6,
                        base_url=BASE_URL,
                        openai_api_key=OPENAI_API_KEY,
                    )
                    # プロンプトメッセージを渡してモデルから応答を受信
                    response = chat_model.invoke(messages)
                    # 完全な応答テキストを取得
                    assistant_response = response.content
                    # チャット履歴にアシスタントの応答を記録
                    st.session_state.chat_history[-1]["assistant"] = assistant_response
                except Exception as e:
                    # エラー発生時にエラーメッセージを表示
                    st.error(f"エラーが発生しました: {str(e)}")
        # 次回のフォーム作成のためにform_keyをインクリメントし、ウィジェットを再生成
        st.session_state.form_key += 1
        # 状態の更新後、ページ全体を再読み込み
        st.rerun()

# -----------------------------------------------------------------------------
# このスクリプトが直接実行された場合にmain()関数を呼び出す
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
