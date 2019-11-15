
import requests
import json
import pymysql
import time

from datetime import datetime

conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')

SAMPLING_DELAY = 20
OWHAT_DELAY = 3


def owhat_project_amount(project_id):
    """
        Description:
            This function is to calculate the total amount of a given owhat amount project.
        Parameter:
            project_id: numeric id of a a owhat amount project
        Author: Lu.Biq Pan
        Date: September 2019
    """
    # Request parameters.
    url_detail = "http://appo4.owhat.cn/api?v=1.0&cmd_m=findPricesAndStock&client=%7B%22deviceid%22%3A%22bed3ac48" \
                 "-fe48-3b11-b174-15538ed5ba61%22%2C%22platform%22%3A%22android%22%2C%22version%22%3A%225.5." \
                 "0%22%2C%22channel%22%3A%22owhat_app%22%7D&cmd_s=shop.price&requesttimestap=1522855734352"
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }
    data = {
        "data": json.dumps({"fk_goods_id": project_id})
    }

    # Request by post.
    resp = requests.post(url=url_detail, data=data, headers=headers)
    # Return data successfully.
    if resp.json()['result'] == 'success':
        # Resolve json.
        return_dict = resp.json()
        data_dict = return_dict['data']
        prices_list = data_dict['prices']

        # Calculate total sale.
        i = 0
        total_sale = 0
        sale = []
        for item in prices_list:
            sale.append(float(item['price']) * int(item['salestock']))
        while i < len(sale):
            total_sale = total_sale + sale[i]
            i = i + 1
        return total_sale

    # Return data failed.
    else:
        print('Owhat returns data failed. Fail message: %s.' % resp.json()['message'])
        return 0


def get_exist_projects():
    exist_project_list = []

    # Connect database.
    cursor = conn.cursor()  # Create cursor.

    # Get owhat_id from table fanclubs.
    sql = "SELECT project_id FROM project WHERE platform = 'owhat'"
    cursor.execute(sql)

    for field in cursor:
        if field[0] != '' and field[0] is not None:
            exist_project_list.append(field[0])

    return exist_project_list


def get_fan_club():
    fan_club_list = []

    # Connect database.
    cursor = conn.cursor()  # Create cursor.

    # Get owhat_id from table fanclubs.
    sql = "SELECT owhat_id FROM fan_club WHERE active = 1"
    cursor.execute(sql)

    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append(field[0])

    return fan_club_list


def sample_exist_owhat_project(exist_project_list):
    cursor = conn.cursor()

    for project_id in exist_project_list:
        time.sleep(OWHAT_DELAY)
        # Calculate total amount.
        amount = owhat_project_amount(project_id)

        # Update.
        try:
            update_data = (amount, datetime.now(), project_id)
            sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s"
            cursor.execute(sql, update_data)
            conn.commit()
        except cursor.Error as e:
            conn.rollback()
            print("Updating owhat project failed. project_id = %s. Error: %s" % (project_id, e))


def sample_new_owhat_project(fan_club_list):
    # for fan_club in fan_club_list:
    for fan_club in ['854446']:
        # Delay.
        time.sleep(OWHAT_DELAY)

        # Owhat API parameters.
        headers = {
            'host': 'm.owhat.cn',
            'content-type': 'application/x-www-form-urlencoded'
        }
        url = "https://m.owhat.cn/api?requesttimestap=" + str(int(time.time() * 1000))
        data = '{"pagenum":1,"pagesize":20,"userid": ' + fan_club + ',"tabtype": 1}'
        params = {
            'cmd_s': 'userindex',
            'cmd_m': 'home',
            'v': '1.0.0L',
            'client': '{"platform":"mobile","version":"1.0.0L","deviceid":"6193fcd0-5134-16ba-1425-8737ab1f69d3",'
                      '"channel":"owhat"}',
            'data': data
        }

        # Request by post and response.
        resp = requests.post(url, params, json=True, headers=headers)
        return_dict = resp.json()
        print(return_dict)


# Update Owhat projects that can not be sampled from fan club profile page.
def update_odd_owhat():
    # Connect database.
    cursor = conn.cursor()  # Create cursor.
    sql = "SELECT project_id FROM project WHERE remark = 'odd' and platform = 'owhat'"
    cursor.execute(sql)

    for field in cursor:
        project_id = field[0]
        print(project_id)
        if project_id != '' and project_id is not None:
            # Calculate total amount of given owhat project.
            amount = owhat_project_amount(project_id)
            print(amount)
            # Update.
            update_data = (amount, datetime.now(), project_id)
            sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s and platform = 'owhat'"
            try:
                cursor.execute(sql, update_data)
                conn.commit()
            except conn.Error as e:
                conn.rollback()
                print("Updating owhat project failed. project_id = %s. Error: %s" % (project_id, e))


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


def main():
    # exist_project_list = get_exist_projects()
    # sample_exist_owhat_project(exist_project_list)
    # fan_club_list = get_fan_club()
    # sample_new_owhat_project(fan_club_list)
    # update_odd_owhat()
    # get_modian_project_by_fan_club(1090311)
    amount = owhat_project_amount(23295)
    print(amount)


if __name__ == '__main__':
    main()


