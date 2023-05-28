#!/opt/Anaconda3/2022.05/bin/python
import fcntl
import time
import signal
import os
import subprocess
import sys
import random
import psutil


def kill_proc_tree(pid, including_parent=True):  
    parent = psutil.Process(pid) 
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)

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


def get_task_info(TASKID, queue_info_path):
    with open(queue_info_path, 'r') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        if lines == []:
            fcntl.flock(f, fcntl.LOCK_UN)
            return
        for line in lines:
            task_info = parse_task_info(line)
            if task_info['TASKID'] == TASKID:
                fcntl.flock(f, fcntl.LOCK_UN)
                return task_info


def update_task_status(TASKID, new_status, queue_info_path):
    with open(queue_info_path, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        for i, line in enumerate(lines):
            task_info = parse_task_info(line)
            if task_info['TASKID'] == TASKID:
                task_info['ST'] = new_status
                lines[i] = str(list(task_info.values())).strip('[]').replace("'", "") + '\n'
                break
        f.seek(0)
        f.truncate()
        f.writelines(lines)
        fcntl.flock(f, fcntl.LOCK_UN)



def check_task(queue_info_path,detect_cache_file):
    with open(queue_info_path, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        if lines == []:
            fcntl.flock(f, fcntl.LOCK_UN)
            return
        tasks = [parse_task_info(i) for i in lines]
        for n, task in enumerate(tasks):
            if task['ST'] != 'PD':
                task_id = task['TASKID']
                log_file = f'{detect_cache_file}/task_{task_id}.log'
                task_file = f'{detect_cache_file}/task_{task_id}.sh'
                if os.path.exists(log_file):
                    last_modified = os.path.getmtime(log_file)
                    current_time = time.time()
                    if current_time - last_modified > 5:
                        tasks[n]['ST'] = 'C'
                        if os.path.exists(log_file):
                            os.remove(log_file)
                        if os.path.exists(task_file):
                            os.remove(task_file)
        f.seek(0)
        f.truncate()
        for task in tasks:
            values = list(task.values())
            f.write(str(values).strip('[]').replace("'", "") + '\n')
        fcntl.flock(f, fcntl.LOCK_UN)

           
def get_next_task(queue_info_path,nodelist):
    next_task = None
    with open(queue_info_path, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        # 解析任务信息
        task_info_lines = f.readlines()
        if task_info_lines == []:
            fcntl.flock(f, fcntl.LOCK_UN)
            return None
        parsed_task_info = [parse_task_info(line) for line in task_info_lines]
        for n, task_info in enumerate(parsed_task_info):
            if task_info['ST'] == 'PD':
                # 更新任务状态为 'R'
                parsed_task_info[n]['ST'] = 'R'
                parsed_task_info[n]['NodeList'] = nodelist
                parsed_task_info[n]['Date'] = int(time.time())
                next_task = parsed_task_info[n]
                f.seek(0)
                f.truncate()
                for task_info in parsed_task_info:
                    values = list(task_info.values())
                    f.write(str(values).strip('[]').replace("'", "") + '\n')
                break
        fcntl.flock(f, fcntl.LOCK_UN)
    return next_task


def update_task_info(queue_info_path):
    with open(queue_info_path, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        if lines == []:
            fcntl.flock(f, fcntl.LOCK_UN)
            return
        tasks = [parse_task_info(i) for i in lines]
        tasks = [task for task in tasks if task['ST'] != 'C']
        f.seek(0)
        f.truncate()
        for task in tasks:
            values = list(task.values())
            f.write(str(values).strip('[]').replace("'", "") + '\n')
        fcntl.flock(f, fcntl.LOCK_UN)


def remove_completed_tasks(TASKID,queue_info_path):
    with open(queue_info_path, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        updated_lines = []
        for line in lines:
            task_info = parse_task_info(line)
            if task_info['TASKID'] != TASKID and task_info['ST'] != 'C':
                updated_lines.append(line)
        f.seek(0)
        f.truncate()
        f.writelines(updated_lines)
        fcntl.flock(f, fcntl.LOCK_UN)

def run_task(task_info,queue_info_path,task_cache_file,detect_cache_file):
    TASKID = task_info['TASKID']
    WorkDir = task_info['WorkDir']
    NAME = task_info['NAME']
    # 进入任务的工作目录
    os.chdir(WorkDir)

    # 启动新的进程执行任务，并获取其 PID
    command = [f'{task_cache_file}/task_{TASKID}.sh']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    pid = process.pid

    try:
        # 循环检查任务状态，直到任务完成或被取消
        while process.poll() is None:
            random_flag = random.randint(1, 10000000000)
            time.sleep(2)
            # 读取当前的任务信息，并找到当前任务
            current_task_info = get_task_info(TASKID,queue_info_path)
            if current_task_info is None or current_task_info['ST'] == 'C':
                # 如果任务已经被取消或者消失，尝试杀死任务进程
                kill_proc_tree(pid)
                if current_task_info is not None:
                    remove_completed_tasks(TASKID,queue_info_path)

            # 更新任务日志
            try:
                with open(f'{detect_cache_file}/task_{TASKID}.log', 'w') as f:
                    f.write(f'{NAME} is running, pid is {pid}\n')
                    f.write(f'{random_flag}')
            except Exception as e:
                print(f"Failed to write log file: {e}")
            check_task(queue_info_path,detect_cache_file)
        else:
            update_task_status(TASKID, 'C',queue_info_path)
            remove_completed_tasks(TASKID,queue_info_path)
    finally:
        # 清理任务缓存和日志文件
        try:
            if os.path.exists(f'{task_cache_file}/task_{TASKID}.sh'):
                os.remove(f'{task_cache_file}/task_{TASKID}.sh')
            if os.path.exists(f'{detect_cache_file}/task_{TASKID}.log'):
                os.remove(f'{detect_cache_file}/task_{TASKID}.log')
        except Exception as e:
            print(f"Failed to remove files: {e}")


def main_loop(queue_info_path,task_cache_file,detect_cache_file,nodelist):
    while True:
        time.sleep(5)
        task_to_run = get_next_task(queue_info_path,nodelist)
        if task_to_run is not None:
            run_task(task_to_run,queue_info_path,task_cache_file,detect_cache_file)
        update_task_info(queue_info_path)

if __name__ == '__main__':
    nodelist = sys.argv[1]
    queue_info_path = find_file_path('queue_info.dat')
    task_cache_file=find_file_path('__task_cache__')
    detect_cache_file=find_file_path('__detect_cache__')
    main_loop(queue_info_path,task_cache_file,detect_cache_file,nodelist)





# while True:
#     time.sleep(5)
#     check_task()
#     flag = False
#     #解析queue_info.dat文件
#     with open(queue_info_path, 'r+') as f:
#         # 使用文件锁
#         fcntl.flock(f, fcntl.LOCK_EX)
#         lines = f.readlines()
#         parse_lines = []
#         for i in lines:
#             parse_lines.append(parse_task_info(i))
#         # 从上到下，找到状态为PD的任务，将其状态改为R
#         for n, i in enumerate(parse_lines):
#             if i['ST'] == 'PD':
#                 parse_lines[n]['ST'] = 'R'
#                 parse_lines[n]['NodeList'] = nodelist
#                 flag = True
#                 parse_lines[n]['Date'] = int(time.time())
#                 break

#         # 清空文件内容
#         f.seek(0)
#         f.truncate()

#         # 将修改后的任务信息写入文件
#         for i in parse_lines:
#             values = list(i.values())
#             f.write(str(values).strip('[]').replace("'", "") + '\n')

#         fcntl.flock(f, fcntl.LOCK_UN)

#     if flag:
#         TASKID = parse_lines[n]['TASKID']
#         WorkDir = parse_lines[n]['WorkDir']
#         NAME=parse_lines[n]['NAME']
#         #将任务交到后台执行，并拿到任务的pid
#         os.chdir(WorkDir)
#         command = [f'{task_cache_file}/task_{TASKID}.sh']
#         process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#         pid = process.pid
#         while process.poll() is None:
#             #随机生成一个时间，将其写入到__detect_cache__文件夹中
#             random_flag = random.randint(1, 10000000000)
#             time.sleep(2)
#             #读取现在的queue_info.dat文件，并找到对应的任务
#             with open(queue_info_path, 'r+') as f:
#                 fcntl.flock(f, fcntl.LOCK_EX)
#                 lines = f.readlines()
#                 parse_lines = []
#                 for i in lines:
#                     parse_lines.append(parse_task_info(i))
#                 run_task_info = [i for i in parse_lines if i['TASKID'] == TASKID][0]
#                 task_state = run_task_info['ST']
#                 if task_state == 'C':
#                     #杀死任务进程树
#                     kill_proc_tree(pid)
#                     break
#                 # 清空文件内容
#                 f.seek(0)
#                 f.truncate() 
#                 # 将修改后的任务信息写入文件
#                 for i in parse_lines:
#                     if i['ST'] != 'C':
#                         values = list(i.values())
#                         f.write(str(values).strip('[]').replace("'", "") + '\n')
#                 fcntl.flock(f, fcntl.LOCK_UN)
#                 with open(f'{detect_cache_file}/task_{TASKID}.log', 'w') as f:
#                     f.write(f'{NAME} is running, pid is {pid}\n')
#                     f.write(f'{random_flag}')
#                 check_task()
#         else:
#             with open(queue_info_path, 'r+') as f:
#                 fcntl.flock(f, fcntl.LOCK_EX)
#                 lines = f.readlines()
#                 parse_lines = []
#                 for i in lines:
#                     parse_lines.append(parse_task_info(i))
#                 f.seek(0)
#                 f.truncate()
#                 # 将修改后的任务信息写入文件
#                 for i in parse_lines:
#                     if i['TASKID'] != TASKID:
#                         values = list(i.values())
#                         f.write(str(values).strip('[]').replace("'", "") + '\n')      
#                 fcntl.flock(f, fcntl.LOCK_UN)



#         #将__task_cache__文件夹中的任务脚本删除
#         os.remove(f'{task_cache_file}/task_{TASKID}.sh')
#         #将__detect_cache__文件夹中的任务日志删除
#         os.remove(f'{detect_cache_file}/task_{TASKID}.log')
    

#     update_task_info()
            


