
<img src="https://github.com/yut8a/meishi_image2text/assets/92322168/e66f3bb6-c116-4d53-946f-fa7f96a0a91c" width="500">

名刺の画像の情報をcsv形式で保存するコード\
目的:アルバイト先で名刺の情報の入力の効率化を図るため\
構造(自動化)
1. 名刺の写真を撮る
2. LINEに送る
3. GoogleDriveに保存
4. GoogleDriveからダウンロード
5. 名刺の画像からテキスト情報を抽出
6. CSVで保存

仮想環境の作成
```
python==3.10.11
python -m venv meishi_image2text
pip install -r requirement.txt
```
## 実行手順
1. 同階層に`key.json(Cloud Vision APIキー)`をコピー
2. `image_folder`内にOAuth 2.0 クライアント IDの認証`credential.json`をコピー
3. `python　quickstart.py `をたたくと`token.json`ができる
4. `python download_image.py `内のfolder_IDを画像が保存されているGoogleDriveのフォルダのIDに変更
5. `python download_image.py `を実行し、`image_folder`内の画像ファイル以外を取り出す(png,jpgだけを取り出すように変更すればよい)
6. `image_folder`に撮られた写真がアップロードされる
7. 環境下で`python　meishi_image2text.py `をたたくと各名刺の情報がまとめられたcsvファイルができる(ロゴが非常に大きい名刺はロゴを間違えて名前と認識してしまう可能性が高い)

本コードの参考文献は以下の通り

1. (https://azure-recipe.kc-cloud.jp/cognitive-services-computer-vision-3/)
2. (https://qiita.com/CJHJ/items/52c15ff636c52e93284d)
3. (https://zenn.dev/yamatake/articles/07a108e09232a6)
4. (https://developers.google.com/drive/api/quickstart/python?hl=ja\)
5. (https://developers.google.com/drive/api/guides/manage-downloads?hl=ja)

