import os
import subprocess
#写一个函数，将时间戳转换成day-hour:min:sec格式,例如：01-01:01:01
def time_stamp(time):
    day = time // (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    min = time // 60
    time %= 60
    sec = time
    return "%d-%02d:%02d:%02d" % (day, hour, min, sec)


def parse_task_info(task_info_list):
    task_info_list = task_info_list.replace(' ', '').replace('\n','').split(',')
    head = ['TASKID', 'NAME', 'ST', 'TIME', 'WorkDir', 'Date', 'NodeList']
    task_info = {}
    for n, i in enumerate(head):
        task_info[i] = task_info_list[n]
    return task_info

def find_file(file_name):
    for i in os.environ['PATH'].split(':'):
        if os.path.exists(i + '/' + file_name):
            with open(i + '/' + file_name, 'r') as f:
                lines = f.readlines()
                return lines

def find_file_path(file_name):
    for i in os.environ['PATH'].split(':'):
        if os.path.exists(i + '/' + file_name):
            return i + '/' + file_name
    return None

def run_background_task():
    # 执行后台任务
    command = ["python", "my_script.py", "arg1", "arg2"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 获取后台任务的PID号
    pid = process.pid
    print("Background task PID:", pid)