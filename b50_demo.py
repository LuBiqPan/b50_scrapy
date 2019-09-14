
import requests
from bs4 import BeautifulSoup
import re


def main():
    resp = requests.get('https://zhongchou.modian.com/item/79880.html')
    resp.encoding = 'utf-8'
    # soup = BeautifulSoup(resp.text, "html5lib")
    soup = BeautifulSoup(resp.text, "lxml")

    title = soup.find_all(class_='title')[0].get_text()
    fanclub = soup.find_all(class_='name team clearfix')[0].get_text()
    amount = soup.find_all(class_='col1 project-goal')
    print(soup)


if __name__ == '__main__':
    main()
