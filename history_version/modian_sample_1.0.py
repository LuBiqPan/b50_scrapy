
import requests
import json
import pymysql
import time

from datetime import datetime

# conn = pymysql.connect(user='root', password='password', database='b50_demo', charset='utf8')
conn = pymysql.Connect(
    host="139.196.160.147",
    port=3306,
    user='B50',
    password='MA#MyE*2',
    database='B50',
    charset='utf8'
)

SAMPLING_DELAY = 20
MODIAN_DELAY = 0.5


def update_modian():
    """
        Description:
            This function is to sample and resolve detail information of each given modian amount project.
            Resolved fields include project name, project id, real-time amount, start time, etc.

            For each fan club, sample all projects it issued. Fields resolved are inserted into database
            or updated if the project already existed in database.
        Parameter: none
        Author: Lu.Biq Pan
        Version: 1.0
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

    # Get modian_id from table fanclubs.
    sql = "SELECT modian_id, fanclub, id FROM fanclubs WHERE active = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            fan_club_list.append((field[0], field[1], field[2]))

    # Get project_id from table projects.
    sql = "SELECT project_id FROM projects WHERE platform = '摩点'"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            project_list.append(field[0])

    # Get project_id from table projects which are obsoleted.
    sql = "SELECT project_id FROM projects WHERE platform = '摩点' AND is_obsolete = 1"
    cursor.execute(sql)
    for field in cursor:
        if field[0] != '' and field[0] is not None:
            obsolete_project_list.append(field[0])

    # Sample starts.
    for fan_club_tuple in fan_club_list:
        # Delay.
        time.sleep(MODIAN_DELAY)
        # Sampling of one fan club starts here.
        print("     Sampling of %s." % fan_club_tuple[1])

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
                project_id = int(project.get('id'))
                amount = 0 if project['backer_money'] == '' else float(project['backer_money'])
                # fan_club = project['username']
                # fanclub_id = project.get('user_id')
                fanclub_id = fan_club_tuple[2]
                start_time = project.get('start_time')
                end_time = project.get('end_time')

                # For new project, insert it into table projects.
                if project_id not in project_list:
                    try:
                        new_data = (project_name, project_id, '摩点', amount, fanclub_id,
                                    start_time, end_time, datetime.now(), datetime.now())
                        sql = "INSERT INTO projects(project_name, project_id, platform, amount, fanclub_id, " \
                              "start_time, end_time, created_at, updated_at)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()
                        print("         Inserting new Modian project 《%s》 finished." % project_name)
                    except cursor.Error as e:
                        conn.rollback()
                        print("Inserting modian project failed. Insert data without project_name. "
                              "project_id = %s. Error: %s" % (project_id, e))
                        # Some projects name may include characters which are incompatible with MySQL encoding.
                        # For such projects, insert data without project_name.
                        new_data = (project_id, '摩点', amount, fanclub_id,
                                    start_time, end_time, datetime.now(), datetime.now())
                        sql = "INSERT INTO projects(project_id, platform, amount, fanclub_id, " \
                              "start_time, end_time, created_at, updated_at)" \
                              " VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql, new_data)
                        conn.commit()

                # For project already in table projects but not obsoleted, update amount field only.
                elif project_id not in obsolete_project_list:
                    try:
                        update_data = (amount, datetime.now(), project_id)
                        sql = "UPDATE projects SET amount = %s, updated_at = %s WHERE project_id = %s"
                        cursor.execute(sql, update_data)
                        conn.commit()
                        print("         Updating Modian project 《%s》 finished." % project_name)
                    except cursor.Error as e:
                        conn.rollback()
                        print("Updating modian project failed. project_id = %s. Error: %s" % (project_id, e))

        # Return data failed.
        else:
            print('Modian returns data failed. Status code: %s.' % return_dict['status'])

    # Sampling finished.
    print('Sampling of Modian finished at %s.' % datetime.now())
    # print("#" * 48)


def main():
    try:
        # time.sleep(10)
        while True:
            update_modian()
            time.sleep(SAMPLING_DELAY)
    except Exception as e:
        print("%s \033[31;0m Something wrong.\033[0m %s" % (datetime.now(), e))
    finally:
        # print("Restart.")
        main()


if __name__ == '__main__':
    main()


