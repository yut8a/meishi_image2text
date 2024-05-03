写真で撮った名刺の画像の情報をcsv形式で保存するコード
仮想環境の作成

```
python==3.10.11
python -m venv meishi_image2text
pip install -r requirement.txt
```
同階層に`image_folder`と`key.json(Cloud Vision APIを使用するため)`を作成
`image_folder`にとった名刺の写真を入れる

環境下で`python　meishi_image2text.py `をたたくと各名刺の情報がまとめられたcsvファイルができる

本コードの参考文献は以下の通り

(https://azure-recipe.kc-cloud.jp/cognitive-services-computer-vision-3/)
(https://qiita.com/CJHJ/items/52c15ff636c52e93284d)
