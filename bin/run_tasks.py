#!/opt/Anaconda3/2022.05/bin/python
import fcntl
import time
import signal
import os
import subprocess
import sys
import random

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


def chech_task():
    run_flag = False
    with open(queue_info_path, 'r') as f:
        lines = f.readlines()
        parse_lines = []
        for i in lines:
            parse_lines.append(parse_task_info(i))
    bak_parse_lines = parse_lines.copy()
    # 遍历所有任务的ID
    for n, task_info in enumerate(parse_lines):
        TASKID = task_info['TASKID']
        log_file = f'{detect_cache_file}/task_{TASKID}.log'
        if os.path.exists(log_file):
            # 检查文件的最后修改时间
            last_modified = os.path.getmtime(log_file)
            current_time = time.time()            
            # 如果文件在最近5秒内被修改过，则任务仍在运行
            if current_time - last_modified <= 5:                
                parse_lines[n]['ST']='R'
            else:
                parse_lines[n]['ST']='C'
                run_flag = True
                #将__detect_cache__文件夹中的任务日志删除
                os.remove(f'{detect_cache_file}/task_{TASKID}.log')
    if run_flag:
        # 使用写模式重新打开文件
        with open(queue_info_path, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            for i in parse_lines:
                values = list(i.values())
                f.write(str(values).strip('[]').replace("'", "")+ '\n')
            fcntl.flock(f, fcntl.LOCK_UN)


nodelist = sys.argv[1]
queue_info_path = find_file_path('queue_info.dat')
task_cache_file=find_file_path('__task_cache__')
detect_cache_file=find_file_path('__detect_cache__')

#解析queue_info.dat文件
with open(queue_info_path, 'r') as f:
    lines = f.readlines()
    parse_lines = []
    for i in lines:
        parse_lines.append(parse_task_info(i))

while True:
    time.sleep(5)
    chech_task()
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
            #随机生成一个时间，将其写入到__detect_cache__文件夹中
            random_flag = random.randint(1, 10000000000)
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

            with open(f'{detect_cache_file}/task_{TASKID}.log', 'w') as f:
                f.write(f'{NAME} is running, pid is {pid}\n')
                f.write(f'{random_flag}')
            chech_task()

        #将__task_cache__文件夹中的任务脚本删除
        os.remove(f'{task_cache_file}/task_{TASKID}.sh')
        #将__detect_cache__文件夹中的任务日志删除
        os.remove(f'{detect_cache_file}/task_{TASKID}.log')
    
    # 任务运行完毕，将对应的任务信息从queue_info.dat文件中删除(使用文件锁)
    with open(queue_info_path, 'r') as f:
        # 先读取现在的queue_info.dat文件
        lines = f.readlines()
        parse_lines = []
        for i in lines:
            task_info_ = parse_task_info(i)
            if task_info_['ST'] != 'C':
                parse_lines.append(task_info_)

    # 使用写模式重新打开文件
    with open(queue_info_path, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        for i in parse_lines:
            values = list(i.values())
            f.write(str(values).strip('[]').replace("'", "")+ '\n')
        fcntl.flock(f, fcntl.LOCK_UN)
            
