# 生成AIで「×(カケ)る」八戸オープンデータ

![生成AIで「×(カケ)る」八戸オープンデータ](images/ai_co_create_open_data_hachinohe.png)

## 使用したもの
* [Streamlit](https://streamlit.io/)
* [Ollama](https://ollama.com/)
* https://huggingface.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf
* [八戸市オープンデータ](https://www.city.hachinohe.aomori.jp/gyoseijoho/tokeijoho/opendata/)

## データの取得
1. [八戸市オープンデータコーナー](https://www.city.hachinohe.aomori.jp/soshikikarasagasu/johosystemka/tokeijoho/1/1495.html)からデータをダウンロードし、dataフォルダに置く。
2. PDFは[MarkItDown](https://github.com/microsoft/markitdown)でMarkdownに変換(拡張子md)。
3. データ名、データの種類(csv、excel、md)、ファイル名、URL(実際には使用しない)からなるdata/opendata.xlsxを作る

## Ollamaの準備
1. Ollamaを[ダウンロード](https://ollama.com/download/windows)してインストール
2. Ollamaでrinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latestをpullする。
```
ollama pull hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest
```

## Pythonライブラリのインストール
1. [仮想環境を作る](https://docs.python.org/ja/3.11/library/venv.html)
2. Pandas、Ollama Python Library、Streamlitライブラリをpip installなどでインストール

## 実行
```
streamlit run app.py
```

## 作者
[小久保 温(こくぼ・あつし)](https://akokubo.github.io/)
