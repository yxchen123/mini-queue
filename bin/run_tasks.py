#!/opt/Anaconda3/2022.05/bin_nompi/python
import fcntl
import time
import signal
import os
import subprocess
import sys

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

queue_info_path = find_file_path('queue_info.dat')
nodelist = sys.argv[1]
task_cache_file=find_file_path('__task_cache__')
#解析queue_info.dat文件
with open(queue_info_path, 'r') as f:
    lines = f.readlines()
    parse_lines = []
    for i in lines:
        parse_lines.append(parse_task_info(i))

while True:
    flag = False
    #从上到下，找到状态为PD的任务，将其状态改为R
    for n, i in enumerate(parse_lines):
        if i['ST'] == 'PD':
            parse_lines[n]['ST'] = 'R'
            parse_lines[n]['NodeList'] = nodelist
            flag = True
            #将修改后的parse_lines写入queue_info.dat文件
            with open(queue_info_path, 'w') as f1:
                #使用文件锁
                fcntl.flock(f1, fcntl.LOCK_EX)
                parse_lines[n]['Date'] = int(time.time())
                for i in parse_lines:
                    values = list(i.values())
                    f1.write(str(values).strip('[]').replace("'", "")+ '\n')
                fcntl.flock(f1, fcntl.LOCK_UN)
            break
    if flag:
        TASKID = parse_lines[n]['TASKID']
        WorkDir = parse_lines[n]['WorkDir']
        NAME=parse_lines[n]['NAME']
        #将任务交到后台执行，并拿到任务的pid
        os.chdir(WorkDir)
        command = ["bash", f'{task_cache_file}/task_{TASKID}.sh']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid = process.pid

        while process.poll() is None:
            time.sleep(1)
            #读取现在的queue_info.dat文件，并找到对应的任务
            with open(queue_info_path, 'r') as f:
                lines = f.readlines()
                parse_lines = []
                for i in lines:
                    parse_lines.append(parse_task_info(i))
            run_task_info = [i for i in parse_lines if i['TASKID'] == TASKID][0]
            task_state = run_task_info['ST']
            if task_state == 'C':
                #杀死任务
                os.kill(pid, signal.SIGTERM)
                break

    # 任务运行完毕，将对应的任务信息从queue_info.dat文件中删除(使用文件锁)
    with open(queue_info_path, 'r') as f:
        # 先读取现在的queue_info.dat文件
        lines = f.readlines()
        parse_lines = []
        for i in lines:
            task_info_ = parse_task_info(i)
            if task_info_['TASKID'] != TASKID:
                parse_lines.append(task_info_)

    # 使用写模式重新打开文件
    with open(queue_info_path, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        for i in parse_lines:
            values = list(i.values())
            f.write(str(values).strip('[]').replace("'", "")+ '\n')
        fcntl.flock(f, fcntl.LOCK_UN)
    
    #将__task_cache__文件夹中的任务脚本删除
    os.remove(f'{task_cache_file}/task_{TASKID}.sh')
            
            
