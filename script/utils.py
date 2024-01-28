import subprocess
import os
import time

executionTimeout = 200


def exec_cmd(cmd: str):
    print("command: " + cmd)
    exit_status = os.system(cmd)

    if exit_status == 0:
        print("Command executed successfully")
    else:
        print(f"Command failed with exit status {exit_status}")


def exec_cmd_async(cmd: str):
    print("command: " + cmd)
    popen = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True,
                             bufsize=1)
    return popen


def traverse_dir(dir_name: str) -> list:
    xml_files = []

    # 使用os.walk遍历目标文件夹及其子文件夹
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            if file.startswith('.'):
                continue
            if file.endswith('.xml'):
                # 如果文件以“.xml”后缀结尾，将其添加到列表中
                xml_files.append(os.path.join(root, file))

    return xml_files
