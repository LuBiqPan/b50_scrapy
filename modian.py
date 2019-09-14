import requests
from bs4 import BeautifulSoup
import json
import math
import time
import csv


if __name__ == "__main__":
    home = "https://zhongchou.modian.com"
    url_list = [
        "https://zhongchou.modian.com/item/75492.html"
    ]
    name_list = set()
    money_list = []
    header_list = ["姓名"]
    for url in url_list:
        name_money_map = {}
        res = requests.get(url)
        res.encoding = 'utf-8'
        # soup = BeautifulSoup(res.text, "html5lib")
        soup = BeautifulSoup(res.text, "html5lib")
        title = soup.find_all(class_='title')[0].get_text()
        header_list.append(title)
        proclass = soup.find('input', {'id': 'proClass'}).get('value')
        postid = soup.find('input', {'name': 'post_id'}).get('value')

        comment_url = home+"/comment/ajax_comments"
        data = {
            'page_size': 10,
            'pro_class': proclass,
            'post_id': postid,
            'page': 13
        }
        response = requests.get(comment_url, params=data)
        response.encoding = 'utf-8'
        response_json = json.loads(response.text[31:-2])
        comment_count = int(response_json["comment_count"])

        for i in range(1, int(math.ceil(comment_count/10))+1):
            comment_url = home+"/comment/ajax_comments"
            data = {
                'page_size': 10,
                'pro_class': proclass,
                'post_id': postid,
                'page': i
            }
            response = requests.get(comment_url, params=data)
            response.encoding = 'utf-8'
            response_json = json.loads(response.text[31:-2])
            comment_html = response_json["html"]
            comment_soup = BeautifulSoup(comment_html, "html5lib")
            for comment in comment_soup.findAll(class_="comment-list"):
                name = comment.find(class_="nickname").get_text().strip()
                try:
                    money = float(comment.find(class_="comment-txt").get_text().strip()[4:-1])
                except:
                    continue
                name_list.add(name)
                if name in name_money_map.keys():
                    name_money_map[name] += money
                else:
                    name_money_map[name] = money
            time.sleep(0.2)

        for name in name_money_map:
            name_money_map[name] = round(name_money_map[name], 2)
        money_list.append(name_money_map)

    csv_list = []
    csv_list.append(header_list)
    for name in name_list:
        temp_list = []
        temp_list.append(name)
        for money in money_list:
            if name in money.keys():
                temp_list.append(money[name])
            else:
                temp_list.append(0)
        csv_list.append(temp_list)

    with open('./res.csv', 'w', newline='') as csvfile:
        writer  = csv.writer(csvfile)
        for row in csv_list:
            writer.writerow(row)


