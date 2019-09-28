
import requests
import json
import pymysql
import time


def get_modian_project_by_fan_club(fan_club_id):
    # Request parameters.
    url = 'http://orderapi.modian.com/v45/user/build_product_list'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }
    data = {
        'to_user_id': fan_club_id,
        'page_index': 0,
        'client': 2,
        'page_rows': 10,
        'user_id': 1085377  # Any user_id is ok.
    }
    resp = requests.post(url, data=data, headers=headers)
    return_dict = resp.json()
    print(return_dict)
    project_info = json.loads(return_dict['data'])
    # print(project_info)


if __name__ == '__main__':
    get_modian_project_by_fan_club(1090311)
