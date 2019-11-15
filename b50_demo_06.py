import requests
import time


def owaht_project_starttime_endtime(project_id):
    """
        Description:
            This function is to calculate the start time and end time of a given owhat project.
        Parameter:
            project_id: numeric id of a a owhat amount project.
        Return: Return a dictionary {"start_time": start_time, "end_time": end_time}
        Author: Lu.Biq Pan
        Date: October 2019
    """
    # Request parameters.
    headers = {
        'host': 'm.owhat.cn',
        'content-type': 'application/x-www-form-urlencoded'
    }
    url = "https://m.owhat.cn/api?requesttimestap=" + str(int(time.time() * 1000))
    data = "{'goodsid':" + str(project_id) + "}"
    params = {
        'cmd_s': 'shop.goods',
        'cmd_m': 'findgoodsbyid',
        'v': '1.0.0L',
        'client': '{"platform":"mobile","version":"1.0.0L","deviceid":"6193fcd0-5134-16ba-1425-8737ab1f69d3",'
                  '"channel":"owhat"}',
        'data': data
    }
    # Request by post.
    resp = requests.post(url, params, json=True, headers=headers)
    return_dict = resp.json()

    # Calculate start time.
    start_timestamp = return_dict.get("data").get("salestartat") / 1000
    start_time_raw = time.localtime(start_timestamp)
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", start_time_raw)
    # Calculate end time.
    end_timestamp = return_dict.get("data").get("saleendat") / 1000
    end_time_raw = time.localtime(end_timestamp)
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", end_time_raw)

    return {"start_time": start_time, "end_time": end_time}


if __name__ == '__main__':
    result = owaht_project_starttime_endtime(25289)
    print(result.get("start_time"), result.get("end_time"))
