
import requests
import json
import pymysql
import time

from datetime import datetime

conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')
# conn = pymysql.connect(user='B50', password='MA#MyE*2', database='B50', charset='utf8')

SAMPLING_DELAY = 20
MODIAN_DELAY = 0.5
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


def update_owhat():
    """
        Description:
            This function is to sample and resolve detail information of each given owhat amount project.
            Resolved fields include project name, project id, real-time amount (calculated by calling
            function owhat_project_amount()), fan club id, etc.

            For each fan club, sample all projects it issued. Fields resolved are inserted into database
            or updated if the project already existed in database.
        Parameter: none
        Author: Lu.Biq Pan
        Date: September 2019
        Reference: https://github.com/MskAdr/owhat_data
    """
    print('Sampling of Owhat started at %s' % datetime.now())

    fan_club_list = []          # Active fanclub.
    project_list = []           # Projects in table project.
    obsolete_project_list = []  # Projects that are obsoleted.
    # Request parameters.
    headers = {
        'host': 'm.owhat.cn',
        'content-type': 'application/x-www-form-urlencoded'
    }
    url = "https://m.owhat.cn/api?requesttimestap=" + str(int(time.time() * 1000))

    # Connect database.
    cursor = conn.cursor()  # Create cursor.

    # Get owhat_id from table fan_club.
    sql = "SELECT owhat_id, fan_club FROM fan_club WHERE active = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1]))

    # Get project_id from table project.
    sql = "SELECT project_id FROM project WHERE platform = 'owhat'"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            project_list.append(field[0])

    # Get project_id from table project which are obsoleted.
    sql = "SELECT project_id FROM project WHERE platform = 'owhat' AND is_obsolete = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            obsolete_project_list.append(field[0])

    # Sample starts.
    for fan_club_tuple in fan_club_list:
        # Delay.
        time.sleep(OWHAT_DELAY)
        # Sampling of one fan club starts here.
        # print("     Sampling of %s." % fan_club_tuple[1])

        # Owhat API parameters.
        data = '{"pagenum":1,"pagesize":20,"userid": ' + str(fan_club_tuple[0]) + ',"tabtype": 1}'
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
        if return_dict['result'] == 'success' and return_dict['data'].get('useractivity') is not None:
            # projects = return_dict['data']['useractivity']  # Project list.
            projects = return_dict['data'].get('useractivity')  # Project list.
            for project in projects:
                project_name = project.get('title')
                project_id = project.get('entityid')
                amount = owhat_project_amount(project.get('entityid'))
                # fan_club = project['publishername']
                fanclub_id = project.get('publisherid')

                # For new projects, insert them into table project.
                if str(project_id) not in project_list:
                    try:
                        new_data = (project_name, project_id, 'owhat', amount, fanclub_id, datetime.now(), datetime.now())
                        sql = "INSERT INTO project(project_name, project_id, platform, amount, fanclub_id, create_time, update_time)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()
                        # print("         Inserting new Owhat project 《%s》 finished." % project_name)
                    except cursor.Error as e:
                        conn.rollback()
                        print("Inserting owhat project failed. Insert data without project_name. "
                              "project_id = %s. Error: %s" % (project_id, e))
                        # Insert data without project_name.
                        new_data = (project_id, 'owhat', amount, fanclub_id, datetime.now(), datetime.now())
                        sql = "INSERT INTO project(project_id, platform, amount, fanclub_id, create_time, update_time)" \
                              " VALUES(%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()
                # For projects already in table project but not obsoleted, update amount field only.
                elif str(project_id) not in obsolete_project_list:
                    try:
                        update_data = (amount, datetime.now(), project_id)
                        sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s"
                        cursor.execute(sql, update_data)
                        conn.commit()
                        # print("         Updating Owhat project 《%s》 finished." % project_name)
                    except:
                        conn.rollback()
                        print("Updating owhat project failed. project_id = %s" % project_id)

        # Return data failed.
        else:
            print('Owhat returns data failed. project_id: %s.' % project_id)

    # Update finished.
    print("Sampling of Owhat finished at %s." % datetime.now())
    print("#" * 48)
    print("\n")


def update_modian():
    """
        Description:
            This function is to sample and resolve detail information of each given modian amount project.
            Resolved fields include project name, project id, real-time amount, start time, etc.

            For each fan club, sample all projects it issued. Fields resolved are inserted into database
            or updated if the project already existed in database.
        Parameter: none
        Author: Lu.Biq Pan
        Date: September 2019
    """
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
    sql = "SELECT modian_id, fan_club FROM fan_club WHERE active = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1]))

    # Get project_id from table project.
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
        time.sleep(MODIAN_DELAY)
        # Sampling of one fan club starts here.
        # print("     Sampling of %s." % fan_club_tuple[1])

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
            for project in projects:
                project_name = project.get('name')
                project_id = project.get('id')
                amount = 0 if project['backer_money'] == '' else float(project['backer_money'])
                # fan_club = project['username']
                fanclub_id = project.get('user_id')
                start_time = project.get('start_time')
                end_time = project.get('end_time')

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
                        # print("         Inserting new Modian project 《%s》 finished." % project_name)
                    except cursor.Error as e:
                        conn.rollback()
                        print("Inserting modian project failed. Insert data without project_name. "
                              "project_id = %s. Error: %s" % (project_id, e))
                        # Insert data without project_name.
                        new_data = (project_id, '摩点', amount, fanclub_id,
                                    start_time, end_time, datetime.now(), datetime.now())
                        sql = "INSERT INTO project(project_id, platform, amount, fanclub_id, " \
                              "start_time, end_time, create_time, update_time)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()

                # For project already in table project but not obsoleted, update amount field only.
                elif project_id not in obsolete_project_list:
                    try:
                        update_data = (amount, datetime.now(), project_id)
                        sql = "UPDATE project SET amount = %s, update_time = %s WHERE project_id = %s"
                        cursor.execute(sql, update_data)
                        conn.commit()
                        # print("         Updating Modian project 《%s》 finished." % project_name)
                    except cursor.Error as e:
                        conn.rollback()
                        print("Updating modian project failed. project_id = %s. Error: %s" % (project_id, e))

        # Return data failed.
        else:
            print('Modian returns data failed. Status code: %s.' % return_dict['status'])

    # Sampling finished.
    print('Sampling of Modian finished at %s.' % datetime.now())
    print("#" * 48)
    print("\n")


# Update Owhat projects that can not be sampled from fan club profile page.
def update_odd_owhat():
    # Connect database.
    cursor = conn.cursor()  # Create cursor.
    sql = "SELECT project_id FROM project WHERE remark = 'odd' and platform = 'owhat'"
    cursor.execute(sql)

    for field in cursor:
        project_id = field[0]
        if project_id != '' and project_id is not None:
            # Calculate total amount of given owhat project.
            amount = owhat_project_amount(project_id)
            # Update.
            update_data = (amount, project_id)
            sql = "UPDATE project SET amount = %s WHERE project_id = %s and platform = 'owhat'"
            try:
                cursor.execute(sql, update_data)
                conn.commit()
            except conn.Error as e:
                conn.rollback()
                print("Updating owhat project failed. project_id = %s. Error: %s" % (project_id, e))


def main():
    try:
        # time.sleep(10)
        while True:
            update_owhat()
            update_modian()
            time.sleep(SAMPLING_DELAY)
    except Exception:
        print("%s \033[31;0m Something wrong.\033[0m" % datetime.now())
        print(Exception.__context__)
    finally:
        print("Restart.")
        main()


if __name__ == '__main__':
    main()


