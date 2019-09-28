import requests
import json
import ast
import pymysql
import time
import chardet

from datetime import datetime

conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')


def update_modian():
    print('Sampling of Modian started at %s' % datetime.now())

    fan_club_list = []          # Active fanclub.
    project_list = []           # Projects in table project.
    obsolete_project_list = []  # Projects that are obsoleted.

    # Request parameters.
    url = 'http://orderapi.modian.com/v45/user/build_product_list'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    # Connect database.
    cursor = conn.cursor()      # Create cursor.

    # Get modian_id from table fan_club.
    cursor.execute('SELECT modian_id, fan_club FROM fan_club WHERE active = 1')
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1]))

    # Get project_id from table project.
    # (now() - end_time) < 4000: Sampling may be executed even after project has closed.
    # sql = "SELECT project_id FROM project " \
    #       "WHERE platform = '摩点' AND is_obsolete = 0 AND now() >= start_time AND (now() - end_time) < 4000"
    sql = "SELECT project_id FROM project WHERE platform = '摩点'"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            project_list.append(field[0])

    # Get project_id from table project which are obsoleted.
    sql = "SELECT project_id FROM project WHERE platform = '摩点' AND is_obsolete = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            obsolete_project_list.append(field[0])

    # Sample starts.
    for fan_club_tuple in fan_club_list:
        # Delay.
        time.sleep(1)

        # Modian API parameters.
        data = {
            'to_user_id': fan_club_tuple[0],
            'page_index': 0,
            'client': 2,
            'page_rows': 10,
            'user_id': 1085377          # Any user_id is ok.
        }
        resp = requests.post(url, data=data, headers=headers)
        return_dict = resp.json()

        # Return data successfully.
        if return_dict['status'] == '0':
            projects = json.loads(return_dict['data'])           # Convert string ro dictionary.
            # print(projects)
            for project in projects:
                project_name = project['name']
                project_id = project['id']
                amount = float(project['backer_money'])
                # amount = float(project['backer_money']) if (type(project['backer_money']) == 'str') else 0
                # fan_club = project['username']
                fanclub_id = project['user_id']
                start_time = project['start_time']
                end_time = project['end_time']

                # For new project, insert it into table project.
                if project_id not in project_list:
                    try:
                        new_data = (project_name, project_id, '摩点', amount, fanclub_id,
                                    start_time, end_time, datetime.now(), datetime.now())
                        sql = "INSERT INTO project(project_name, project_id, platform, amount, fanclub_id, " \
                              "start_time, end_time, create_time, update_time)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()
                    except cursor.Error as e:
                        conn.rollback()
                        print("Insert modian project failed. project_id = %s. Error: %s" % (project_id, e))
                        print(project_name)
                # For project already in table project but not obsoleted, update amount field only.
                elif project_id not in obsolete_project_list:
                    try:
                        update_data = (amount, datetime.now(), project_id)
                        sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s"
                        cursor.execute(sql, update_data)
                        conn.commit()
                    except cursor.Error as e:
                        conn.rollback()
                        print("Update modian project failed. project_id = %s. Error: %s" % (project_id, e))

        # Return data failed.
        else:
            print('Modian returns data failed. Status code: %s.' % return_dict['status'])

        # Sampling of one fan club finished.
        print("     Sampling of %s finished." % fan_club_tuple[1])

    # Sampling finished.
    print('Sampling of Modian finished at %s.' % datetime.now())


def get_modian_projects(fan_club_id):
    retry_count = 3
    # Request parameters.
    url = 'http://orderapi.modian.com/v45/user/build_product_list'
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }

    # Modian API parameters.
    data = {
        'to_user_id': fan_club_id,
        'page_index': 0,
        'client': 2,
        'page_rows': 10,
        'user_id': 1085377  # Any user_id is ok.
    }
    resp = requests.post(url, data=data, headers=headers)
    return_dict = resp.json()
    status = return_dict['status']
    message = return_dict['message']
    data = json.loads(return_dict['data'])

    project_name = {"name": "Null"} if len(data) == 0 else data[0]
    print(fan_club_id, resp.status_code, status, message, project_name['name'])
    # while resp.status_code != 200 and retry_count >= 0:
    #     print("Request failed, try again.")
    #     retry_count -= retry_count
    #     time.sleep(TRY_AGAIN_DELAY)
    #     resp = requests.post(url, data=data, headers=headers)
    # retry_count = 3
    # print(resp.status_code)
    # amount = 0 if data[0]['backer_money'] == '' else float(data[0]['backer_money'])
    # print(amount)
    # print(type(data[1]['backer_money']) == 'str')


def get_owhat_projects(fan_club_id):
    headers = {
        'host': 'm.owhat.cn',
        'content-type': 'application/x-www-form-urlencoded'
    }
    url = "https://m.owhat.cn/api?requesttimestap=" + str(int(time.time() * 1000))
    data = '{"pagenum":1,"pagesize":20,"userid": ' + str(fan_club_id) + ',"tabtype": 1}'
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
    print(return_dict["data"].get("anliinfo"))


def get_fan_club_list():
    fan_club_list = []  # Active fanclub.
    cursor = conn.cursor()  # Create cursor.

    # Get modian_id from table fan_club.
    cursor.execute('SELECT modian_id, fan_club FROM fan_club WHERE active = 1')
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append(field[0])
    return fan_club_list


def loop(fan_club_list, count):
    for fan_club_id in fan_club_list:
        get_modian_projects(fan_club_id)
        time.sleep(0.5)
        count = count + 1
        print(count)


if __name__ == '__main__':
    # update_owhat()
    # update_modian()
    # main()
    get_owhat_projects(7984069)
