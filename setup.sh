#!/bin/bash

setup_path=$PWD
PYTHON=`which python`

#将bin目录下的qqa、qqw、run_task.py、sscancel、ssbatch的第一行的python路径改为当前python路径
sed -i "1s@.*@#!$PYTHON@" $setup_path/bin/qqa
sed -i "1s@.*@#!$PYTHON@" $setup_path/bin/qqw
sed -i "1s@.*@#!$PYTHON@" $setup_path/bin/run_tasks.py
sed -i "1s@.*@#!$PYTHON@" $setup_path/bin/sscancel
sed -i "1s@.*@#!$PYTHON@" $setup_path/bin/ssbatch


#将bin目录设置在环境变量,判断是否已经存在，如果存在则不添加
if ! grep -q "export PATH=$setup_path/bin:\$PATH" ~/.bashrc; then
    echo "export PATH=$setup_path/bin:\$PATH" >> ~/.bashrc
fi

#将__task_cache__目录设置在环境变量,判断是否已经存在，如果存在则不添加
if ! grep -q "export PATH=$setup_path/__task_cache__:\$PATH" ~/.bashrc; then
    echo "export PATH=$setup_path/__task_cache__:\$PATH" >> ~/.bashrc
fi

#将setup_path目录设置在环境变量,判断是否已经存在，如果存在则不添加
if ! grep -q "export PATH=$setup_path:\$PATH" ~/.bashrc; then
    echo "export PATH=$setup_path:\$PATH" >> ~/.bashrc
fi



