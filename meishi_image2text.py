import json
import re
import io
from google.cloud import vision
from google.oauth2 import service_account
import csv
import os
from shapely.geometry import MultiPoint
from PIL import Image, ImageDraw

def detect_text(path):
    """画像でのテキストを認識"""
    # クライアントを初期化
    credentials = service_account.Credentials.from_service_account_file('key.json')
    client = vision.ImageAnnotatorClient(credentials=credentials)
    # APIに画像を送信し、結果を格納する
    with open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    # アノテーション結果を格納
    # text：response.text_annotations：帰ってきたアノテーション情報
    # text.description：アノテーションされたテキスト
    # text.bounding_poly.vertices：バウンディングボックスの座標
    texts = response.text_annotations

    # 辞書としてアノテーション結果を格納
    results = []
    for text in texts:
        temp = {
            'description': text.description,
            'vertices': [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        }

        results.append(temp)
        
    return results


def merge_annotations(annotations):
    
    sentences = annotations[0]['description'].split("\n")

    # 「今の文章、座標、文章のインデックス」と言う変数を初期化
    temp_sentence = ""
    temp_vertices = []
    cur_index = 0

    # 2番目のアノテーション結果から以下のループを行う
    sum_anotate = []
    for annotation in annotations[1:]:
        # 「今の文章、座標」に、ループしているアノテーション結果（単語、座標）を後ろから追加
        temp_sentence += annotation['description']
        temp_vertices.append(annotation['vertices'])

        # もし現在の「文章インデックス」で指定する参考文章が「今の文章」とマッチすれば、文章情報を格納する
        # ここでスペースを削除する理由としては、Cloud Vision APIでスペースを入れているかどうかは抽出した単語から判断できないから
        if sentences[cur_index].replace(' ', '') == temp_sentence:
            temp_object = {
                'description': sentences[cur_index],
                'vertices': temp_vertices
            }

            sum_anotate.append(temp_object)

            # 「今の文章、座標」と言う変数を初期化、「文章のインデックス」を1で足す
            temp_sentence = ""
            temp_vertices = []
            cur_index += 1

    return sum_anotate

def draw_boundaries(annotations):
    # 凸包を取得
    convex_hulls = []
    for annotation in annotations:
        # 座標の集合を一個のリストとしてまとめる
        vertices = annotation['vertices']

        merged_vertices = []
        for vertex_set in vertices:
            for vertex in vertex_set:
                merged_vertices.append(vertex)

        # 点集合からMultiPointにして、それの凸包を求め、その凸包を構成する座標の集合を取得
        convex_hull = MultiPoint(
            merged_vertices).convex_hull.exterior.coords
        convex_hulls.append(list(convex_hull))

    return convex_hulls
def make_sentence_bounding_box_list(sum_anotate,sentence_bounding_boxes):
    sentence_bounding_box_list = []
    for cnt in range(len(sum_anotate)):
        name = sum_anotate[cnt]["description"]
        sentence_bounding_box = sentence_bounding_boxes[cnt]
        sentence_bounding_box_set = {
        "name":name,
        "bounding_box":sentence_bounding_box
    }
        sentence_bounding_box_list.append(sentence_bounding_box_set)
    return sentence_bounding_box_list

def calculate_max_height_index(result):
    y_result = []
    for i in range(len(result)):
        y = []
        bounding_box = result[i]["bounding_box"]
        for j in range(len(bounding_box)):
            y.append(bounding_box[j][1])
        y_result.append(max(y)-min(y))
    max_value = max(y_result)
    max_index = y_result.index(max_value)
    return max_index

def remove_noise_words(word,remove_words_list,data):
    table = str.maketrans({
    '\u3000': '',
    ' ': '',
    '\t': ''
    })
    for remove_word in remove_words_list:
        if data[word].lower().find(remove_word) >=0:
            word_arr = data[word].lower().split(remove_word)
            print(word_arr)
            if word_arr[1][0]==":":
                extract_word = word_arr[1][1:len(word_arr[1])]
            else:
                extract_word = word_arr[1]
            print(extract_word)
            data[word] = extract_word.translate(table)
    return data

def extract_postal_code(data):
    postal_code_pattern = r'\d{3}-\d{4}' # 000-0000の形式を郵便番号と仮定
    string = data["post_number"]
    postal_code_match = re.search(postal_code_pattern, string)
    if postal_code_match:
        data["post_number"] = postal_code_match.group()
    return data

def extract_email(data):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    string = data["mail"]
    email_match = re.search(email_pattern, string)
    if email_match:
        data["mail"] = email_match.group()
    return data

def extract_phone_number(data,word):
    phone_number_pattern = r'\b\d{2,4}-\d{2,4}-\d{4}\b'  # 00-0000-0000の形式を電話番号と仮定
    string = data[word]
    phone_number_match = re.search(phone_number_pattern, string)
    if phone_number_match:
        data[word] = phone_number_match.group()
    return data

def make_json_meishi_data(image_path,search_words,prefectures):
    data = {}
    table = str.maketrans({
    '\u3000': '',
    ' ': '',
    '\t': ''
    })
    
    annotations = detect_text(image_path)
    sum_anotate = merge_annotations(annotations)
    sentence_bounding_boxes = draw_boundaries(sum_anotate)
    result = make_sentence_bounding_box_list(sum_anotate,sentence_bounding_boxes)
    
    texts = annotations[0]["description"].split("\n")
    for text in texts:
        for key, words in search_words.items():
            if data.get(key) == None:
                data.update({key: ""})

            word_match = re.search("|".join(words),text.lower())
            if word_match and data[key] == "":
                data[key] = text
        
        #郵便番号と電話番号の差異から郵便番号を判定する(〒の画像判定が難しいため)addressnumberに郵便番号と住所の一行が入る可能性あり
        p1 = re.search(r'^〒', text)
        p2 = re.search(r'\d{3}\-\d{4}$', text)
        p3 = re.search(r'\b\d{2,4}-\d{2,4}-\d{4}\b', text)
        if bool(p1) or bool(p2):
            if bool(p3)==False:
                data["post_number"] =text
                        
    #TEとFAXが一行にまたがる場合は分離    
    if data["tel"].lower().find("fax") >= 0:
        tel_arr = data["tel"].lower().split("fax")
        data["tel"] = tel_arr[0].replace("tel","").translate(table)
        data["fax"] = tel_arr[1].translate(table)
                
    #一行に郵便番号と住所が混在する際の処理　郵便番号と住所を分割する
    flag = False
    for prefecture in prefectures:
        if flag==True:
            break
        for address in ["address","post_number"]:
            if data[address].lower().find(prefecture) >= 0:
                adress_arr = data[address].lower().split(prefecture)
                if len(adress_arr[0]) == 0:
                    pass
                else:
                    data["post_number"] =adress_arr[0]
                    data["address"] = prefecture+adress_arr[1]
                    flag = True
                    break

    #電話番号の処理
    data = extract_phone_number(data,"tel")
    data = extract_phone_number(data,"mobile")
    data = extract_phone_number(data,"fax")
    #郵便番号の処理
    data = extract_postal_code(data)
    #メールアドレスの変更
    data = extract_email(data)
    #名前の抽出
    name_index = calculate_max_height_index(result)
    data["name"] = result[name_index]["name"]
    
    return data

def main():
    prefectures = []
    with open("./prefectures.json", "r",encoding="utf-8") as f:
        di = json.load(f)
        for prefectre_num in range(len(di["prefectures"])):
            prefecture = di["prefectures"][prefectre_num]["name"]

            prefectures.append(prefecture)
    search_words = {
            "company": ["会社"],
            "name":[],
            "position": ["役","部","課","部門","代表","科","ター","士"],
            "mail": ["@", "＠"],
            "tel": ["tel"],
            "mobile":["phone","mobile","携","带","帯"],
            "fax": ["fax"],
            "address": prefectures,
            "url": ["http", "www"]
        }
    
    image_folder = os.listdir("./image_folder")
    os.path.join
    data_list = []
    for image in image_folder:
        image_path = os.path.join("image_folder", image)
        data = make_json_meishi_data(image_path,search_words,prefectures)
        data_list.append(data)
        
    with open("meishi.csv", "w",encoding='utf-8',newline="") as f:
        writer = csv.DictWriter(f, fieldnames =list(data.keys()))
        writer.writeheader()
        writer.writerows(data_list)
    

if __name__ == "__main__":
    main()