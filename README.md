# 生成AIで「×(カケ)る」八戸オープンデータ

![生成AIで「×(カケ)る」八戸オープンデータ](images/ai_co_create_open_data_hachinohe.png)

## 説明資料
[説明資料](https://github.com/akokubo/ai_co_create_open_data_hachinohe/blob/main/docs/ai_co_create_open_data_hachinohe.pdf)

## 使用したもの
* [Streamlit](https://streamlit.io/)
* [Ollama](https://ollama.com/)
* https://huggingface.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf
* [八戸市オープンデータ](https://www.city.hachinohe.aomori.jp/gyoseijoho/tokeijoho/opendata/)

## インストール
```
git clone https://github.com/akokubo/ai_co_create_open_data_hachinohe.git
cd ai_co_create_open_data_hachinohe
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install openpyxl pandas ollama streamlit
mkdir data
```
※Windowsの場合、WSL2の[新しいもの](https://github.com/microsoft/WSL/releases/)をインストールし、アップデート&アップグレードし、python3-pipやpython3.12-venvなどなどをインストールしてからご利用ください。

※仮想環境は、condaなどでもいい。

## データの取得
1. [八戸市オープンデータコーナー](https://www.city.hachinohe.aomori.jp/soshikikarasagasu/johosystemka/tokeijoho/1/1495.html)からデータをダウンロードし、dataフォルダに置く。
2. PDFは[MarkItDown](https://github.com/microsoft/markitdown)でMarkdownに変換(拡張子md)。
3. データ名、データの種類(csv、excel、md)、ファイル名(data/からはじまる)、URL(実際には使用しない)からなるdata/opendata.xlsxを作る
![data/opendata.xlsxの例](images/opendata.xlsx.png)

※プログラムには八戸市のオープンデータ向けのプロンプトを書いているが、プロンプト部分を書き換えれば八戸市のオープンデータに限らず利用できる。

## Ollamaの準備
1. Ollamaをインストール
   - Windowsの場合は、WSL2で仮想環境から `curl -fsSL https://ollama.com/install.sh | sh` でインストール
   - Macの場合は、[ダウンロード](https://ollama.com/download/windows)してインストール
2. Ollamaで大規模言語モデルの `hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest` をpullする。
```
ollama pull hf.co/rinna/deepseek-r1-distill-qwen2.5-bakeneko-32b-gguf:latest
```
※PCのスペックに合わせて大規模言語モデルは選ぶ必要がある。デフォルトで指定しているモデルは12GB程度あるので、PCのスペックが必要になる。小さいモデルには、たとえば2.8GBの `lucas2024/gemma-2-2b-jpn-it:q8_0` などがある。別のモデルを使うときは、そのモデルをpullして、app.pyの1行目を書き換える。

## 実行
最初に、プログラムを展開したフォルダに入る。
次に仮想環境に入っていない場合(コマンドプロンプトに(venv)と表示されていないとき)、仮想環境に入る。
```
source venv/bin/activate
```

Ollamaが起動していないかもしれないので、仮想環境に入っている状態で、大規模言語モデルのリストを表示する(すると起動していなければ、起動する)。
```
ollama list
```

仮想環境に入っている状態で、以下のコマンドでアプリを起動する。
```
python3 -m streamlit run app.py
```

## 作者
[小久保 温(こくぼ・あつし)](https://akokubo.github.io/)

## ライセンス
[MIT License](LICENSE)
