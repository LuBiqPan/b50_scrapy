
import requests
import hashlib
import json
import ast
import pymysql
import time
import datetime

from bs4 import BeautifulSoup
from datetime import datetime

conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')


def main():
    mydict = {}
    # Modian API URL.
    url = 'http://orderapi.modian.com/v45/product'
    data = {
        'pro_id': 79880,
    }
    resp = requests.post(url, data)
    # Return data.
    return_dict = resp.json()
    # Return data successfully.
    if return_dict['status'] == '0':
        # Convert string to dictionary.
        return_data = ast.literal_eval(return_dict['data'])

        # Resolve info needed.
        mydict['order_amount'] = return_data['product_info']['backer_money']
        mydict['modian_user_id'] = return_data['product_info']['user_id']
        mydict['modian_user_nickname'] = return_data['product_info']['username']
        mydict['order_timestamp'] = return_data['product_info']['end_time']
        print(mydict)
        return mydict
    else:
        return {}


def owhat_project_amount(project_id):
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


def update_owhat():
    fan_club_list = []          # Active fanclub.
    active_project_list = []    # Projects that are not obsoleted.
    # Request parameters.
    headers = {
        'host': 'm.owhat.cn',
        'content-type': 'application/x-www-form-urlencoded'
    }
    url = "https://m.owhat.cn/api?requesttimestap=" + str(int(time.time() * 1000))

    # Connect database.
    cursor = conn.cursor()  # Create cursor.

    # Get owhat_id from table fan_club.
    cursor.execute('SELECT owhat_id, fan_club FROM fan_club WHERE active = 1')
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1]))

    # Get project_id from table project.
    cursor.execute("SELECT project_id FROM project WHERE platform = 'owhat' AND is_obsolete = 0")
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            active_project_list.append(field[0])
    # Sample starts.
    for fan_club in fan_club_list:
        # Delay.
        time.sleep(3)

        # owhat API parameters.
        data = '{"pagenum":1,"pagesize":20,"userid": ' + str(fan_club[0]) + ',"tabtype": 1}'
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

        # Return data successfully.
        if return_dict['result'] == 'success':
            projects = return_dict['data']['useractivity']  # Project list.
            for project in projects:
                project_name = project['title']
                project_id = project['entityid']
                amount = owhat_project_amount(project['entityid'])
                fan_club = project['publishername']
                fanclub_id = project['publisherid']

                # For new project, insert it into table project.
                if str(project_id) not in active_project_list:
                    try:
                        new_data = (project_name, project_id, 'owhat', amount, fanclub_id, datetime.now(), datetime.now())
                        sql = "INSERT INTO project(project_name, project_id, platform, amount, fanclub_id, create_time, update_time)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()
                    except:
                        conn.rollback()
                        print("Insert failed. project_id = %s" % project_id)
                # For project already in table project, update amount field only.
                else:
                    try:
                        update_data = (amount, datetime.now(), project_id)
                        sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s"
                        cursor.execute(sql, update_data)
                        conn.commit()
                    except:
                        conn.rollback()
                        print("Update failed. project_id = %s" % project_id)

        # Return data failed.
        else:
            print('Owhat returns data failed. Fail message: %s.' % return_dict['message'])

    # Update finished.
    print("Update owhat finished at %s" % datetime.now())


def update_modian():
    print('Sampling started at %s' % datetime.datetime.now())

    fan_club_list = []          # Active fanclub.
    project_list = []           # Projects already exist.
    project_sample = []         # Projects in table sample.
    project_obsolete = []       # Projects obsoleted.
    new_project_count = 0

    # Modian API URL.
    url = 'http://orderapi.modian.com/v45/user/build_product_list'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    # Connect database.
    # conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')
    cursor = conn.cursor()      # Create cursor.

    # Get modian_id from table fan_club.
    cursor.execute('SELECT modian_id, fan_club FROM fan_club WHERE active = 1')
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1]))

    # Get project_id from table project.
    # (now() - end_time) < 4000: Sampling may be executed even after project has closed.
    sql = "SELECT project_id FROM project " \
          "WHERE project_id IS NOT NULL AND platform = '摩点'" \
          "AND now() >= start_time AND (now() - end_time) < 4000"
    cursor.execute(sql)
    for project_id in cursor:
        project_list.append(project_id[0])

    # Get project_id from table sample.
    cursor.execute("SELECT project_id FROM sample WHERE platform = '摩点'")
    for project_id in cursor:
        project_sample.append(project_id[0])
    # project_sample_count = len(project_sample) + 1      # Project quantity in table sample.

    # Get project_id from table obsolete.
    cursor.execute("SELECT project_id FROM obsolete")
    for project_id in cursor:
        project_obsolete.append(project_id[0])

    # Sample starts.
    for fan_club in fan_club_list:
        # Modian API parameters.
        time.sleep(1)
        data = {
            'to_user_id': fan_club[0],
            'page_index': 0,
            'client': 2,
            'page_rows': 10,
            'user_id': 1085377
        }
        resp = requests.post(url, data=data, headers=headers)
        return_dict = resp.json()

        # Return data successfully.
        if return_dict['status'] == '0':
            mydict = return_dict['data']            # Data.
            projects = json.loads(mydict)           # Convert string ro list.

            # Compare sampling project_id with that in table project.
            for project in projects:
                # Projects already exist.
                if project['id'] in project_list and project['id'] not in project_obsolete:
                    # Update table project.
                    update_data = (float(project['backer_money']), project['id'])
                    sql = "UPDATE project SET amount = %s WHERE project_id = %s"
                    try:
                        cursor.execute(sql, update_data)
                        conn.commit()
                    except:
                        conn.rollback()
                # New projects, save to table sample.
                else:
                    new_project_count += 1
                    # print("New project detected. Project name: 《%s》. Fan club: %s. Start time: %s."
                    #       % (project['name'], project['username'], project['start_time']))
                    # Projects not exist in table sample.
                    if project['id'] not in project_sample:
                        new_data = (project['name'], project['id'], '摩点', project['backer_money'],
                                    project['username'], project['start_time'], project['end_time'])
                        sql = "INSERT INTO sample(project_name, project_id, platform, amount, fan_club, start_time, " \
                              "end_time) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        # Insert data to table sample.
                        try:
                            cursor.execute(sql, new_data)
                            conn.commit()
                        except:
                            conn.rollback()

        # Return data failed.
        else:
            print('Modian returns data failed. Status code: %s.' % return_dict['status'])

        # Sampling of one fan club finished.
        print("Sampling of %s finished." % fan_club[1])

    # Sampling finished.
    print('Sampling of Modian finished at %s. %s new project(s) detected.' % (datetime.datetime.now(), new_project_count))


if __name__ == '__main__':
    update_owhat()
    # owhat_project_amount(72719)
    # demo()
    # main()
    # update_modian()
