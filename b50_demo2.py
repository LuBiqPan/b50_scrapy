
import requests
import hashlib
import json
import ast
import pymysql
import time
import datetime
from bs4 import BeautifulSoup

DELAY = 5                   # Delay in second.


def main():
    url = 'http://orderapi.modian.com/v45/product'
    data = {
        'pro_id': 79880,
    }
    resp = requests.post(url, data)
    # resp.encoding = 'utf-8'
    return_dict = resp.json()
    return_data = ast.literal_eval(return_dict['data'])         # Convert string to dictionary.
    # print(return_data)
    project_id = return_data['product_info']['id']
    project = return_data['product_info']['name']
    total_amount = return_data['product_info']['backer_money']
    start_time = return_data['product_info']['start_time']
    end_time = return_data['product_info']['end_time']
    support_no = return_data['product_info']['backer_count']
    # print('project_id', project_id,)
    print(start_time, end_time)


def update_modian():
    fan_club_list = []          # Active fanclub.
    project_list = []           # Projects already exist.
    project_sample = []         # Projects in table sample.
    # Modian API URL.
    url = 'http://orderapi.modian.com/v45/user/build_product_list'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    # Connect database.
    conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')
    cursor = conn.cursor()      # Create cursor.

    # Get modian_id from table fan_club.
    cursor.execute('SELECT modian_id FROM fan_club WHERE active = 1')
    for modian_id in cursor:
        if modian_id[0] != '' and modian_id[0] is not None:
            fan_club_list.append(modian_id[0])

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

    # Sample starts.
    for fan_club in fan_club_list:
        # Modian API parameters.
        time.sleep(1)
        data = {
            'to_user_id': fan_club,
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
                print(project)
                # Projects already exist.
                if project['id'] in project_list:
                    # print('Project %s already exists.' % (project['id']))
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
            print('Return data failed. Status code: %s.' % return_dict['status'])


if __name__ == '__main__':
    # main()
    update_modian()
    # while True:
    #     update_modian()
    #     time.sleep(DELAY)
    #     print('Running...', datetime.datetime.now())
