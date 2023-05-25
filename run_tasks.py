#!/Users/chenyanxu/opt/anaconda3/bin/python
from tool import *
import fcntl
import time
import signal
queue_info_path = find_file_path('queue_info.dat')

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
            flag = True
            #将修改后的parse_lines写入queue_info.dat文件
            with open(queue_info_path, 'w') as f1:
                #使用文件锁
                fcntl.flock(f1, fcntl.LOCK_EX)
                parse_lines[n]['Date'] = time.time()
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
        command = ["bash", NAME]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid = process.pid

        while os.path.exists('/proc/' + str(pid)):
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
                os.kill(pid, signal.SIGKILL)
        #任务运行完毕，将对应的任务信息从queue_info.dat文件中删除(使用文件锁)
        with open(queue_info_path, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            for i in parse_lines:
                if i['TASKID'] != TASKID:
                    values = list(i.values())
                    f.write(str(values).strip('[]').replace("'", "")+ '\n')
            fcntl.flock(f, fcntl.LOCK_UN)
            
            
