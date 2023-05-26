from tool import *
import time

detect_cache_file=find_file_path('__detect_cache__')
queue_info_path = find_file_path('queue_info.dat')

while True:
    with open(queue_info_path, 'r') as f:
        lines = f.readlines()
        parse_lines = []
        for i in lines:
            parse_lines.append(parse_task_info(i))
    bak_parse_lines = parse_lines.copy()
    # 遍历所有任务的ID
    for task_info in parse_lines:
        TASKID = task_info['TASKID']
        log_file = f'{detect_cache_file}/task_{TASKID}.log'
        if os.path.exists(log_file):
            # 检查文件的最后修改时间
            last_modified = os.path.getmtime(log_file)
            current_time = time.time()            
            # 如果文件在最近5秒内被修改过，则任务仍在运行
            if current_time - last_modified <= 5:                
                parse_lines['ST']='R'
            else:
                parse_lines['ST']='C'
        


    # 每5秒检查一次任务状态
    time.sleep(5)
