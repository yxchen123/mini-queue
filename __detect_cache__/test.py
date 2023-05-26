def check_tasks():
    while True:
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
                    print(f'Task {TASKID} is still running.')
                else:
                    print(f'Task {TASKID} has finished.')

        # 每5秒检查一次任务状态
        time.sleep(5)

# 创建后台任务
pid = os.fork()
if pid == 0:
    check_tasks()

print(1)
