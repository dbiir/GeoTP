#!/usr/bin/python3
import argparse
import os
import sys
import threading
import time
import signal
from datetime import datetime
from itertools import product

import utils
import set_delay as step1

scenarios = ['normal', 'country_emu', 'city_emu', "back_0", "back_1", "back_2", "dynamic", "variance1", "variance2", "variance3", "variance4", "variance5"]
algorithms = ["none", "a", "aharp", "aharp_pa", "aharp_lppa"]
functions = ["dis_ratio", "skew", "wr_ratio", "scalability", "payment", "neworder", "mixed", "dynamic", "variance"]
workloads = ["ycsb", "tpcc"]
engines = ["mysql", "postgresql"]

# path
ssp_path = "/data/apache-shardingsphere-5.3.3-SNAPSHOT-shardingsphere-proxy-bin/bin/"
agent_path = "/data/Agent/target/"
benchbase_path = "/data/"
benchbase_ip = "11.127.237.44"
datasource_ip = ["11.99.55.8", "11.99.55.9", "11.99.55.12", "11.129.111.12"]
emu_cnt = 10


def exit(signum, frame):
    assert (signum == signal.SIGINT or signum == signal.SIGTERM)
    utils.exec_cmd("bash " + ssp_path + "stop.sh")
    utils.exec_cmd("rm -rf /data/apache-shardingsphere-5.3.3-SNAPSHOT-shardingsphere-proxy-bin/logs")
    for ds_ip in datasource_ip:
        exec_cmd = "ps -ef | grep sspagent | grep -v grep | awk '{print $2}' | xargs kill -9"
        utils.exec_cmd("ssh " + ds_ip + " \" " + exec_cmd + "\"")

    exec_cmd = "ps -ef | grep benchbase | grep -v grep | awk '{print $2}' | xargs kill -9"
    utils.exec_cmd("ssh " + benchbase_ip + " \" " + exec_cmd + "\"")

    exec_cmd = "java -classpath /data/XARecoverProject/target/classes:/root/.m2/repository/com/mysql/mysql-connector" \
               "-j/8.0.31/mysql-connector-j-8.0.31.jar:/root/.m2/repository/com/google/protobuf/protobuf-java/3.19.4" \
               "/protobuf-java-3.19.4.jar:/root/.m2/repository/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar" \
               ":/root/.m2/repository/org/checkerframework/checker-qual/3.31.0/checker-qual-3.31.0.jar " \
               "org.dbiir.harp.Main"
    utils.exec_cmd(exec_cmd)

    utils.exec_cmd("./unset_delay.py")
    sys.exit()


signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scenario", dest='scenario', nargs='+', type=str,
                        help="specify the simulation scenario")
    parser.add_argument("-a", "--algorithm", dest='alg', nargs='+', choices=algorithms, type=str,
                        help="specify the algorithm")
    parser.add_argument("-f", "--function", dest='func', nargs='+', choices=functions, type=str,
                        help="specify the function")
    parser.add_argument("-w", "--workload", dest='wl', choices=workloads, type=str, required=True,
                        help="specify the workload")
    parser.add_argument("-e", "--engine", dest="engine", choices=engines, type=str, required=True,
                        help="specify the workload")

    return parser.parse_args()


def set_delay_by_scenario(s):
    if s == "dynamic" or s.__contains__("variance"):
        pass
    else:
        utils.exec_cmd("./set_delay.py -s " + s)


def run_once(s: str, a: str, f: str):
    set_delay_by_scenario(s)
    print("scenario:", s, "algorithm:", a, "function:", f)
    processes = []

    # 1. start the geo-agent
    for ds_ip in datasource_ip:
        exec_cmd = "./bin/start.sh --alg=" + a
        processes.append(utils.exec_cmd_async("ssh " + ds_ip + " \"cd " + agent_path + " ; " + exec_cmd + " &\""))

    # while True:
    #     time.sleep(60)
    time.sleep(30)

    # 2. start the middleware
    start_arg = ""
    if a != "none":
        start_arg = start_arg + "--" + a
    utils.exec_cmd("bash " + ssp_path + "start.sh " + start_arg)

    # while True:
    #     time.sleep(60)
    time.sleep(45)

    # 3.1 generate benchbase config and scp to benchbase node
    # 3.1 run benchbase
    benchbase_dir = benchbase_path + "benchbase-" + args.engine + "/"
    if args.wl == "ycsb":
        # traverse the dir
        local_dir_name = "../config/ycsb_" + f + "/"
        dir_name = "config/" + args.engine + "/ycsb_" + f + "/"
        for conf_file in utils.traverse_dir(local_dir_name):
            unique_ts = datetime.now().strftime('%Y%m%d%H%M%S')
            result_file = os.path.splitext(os.path.basename(conf_file))[0]
            if s != "dynamic":
                print("Run config - { " + result_file + " }")
                java_cmd = "java -jar benchbase.jar -b ycsb -c " + dir_name + os.path.basename(
                    conf_file) + " --execute=true -d " + result_file
                utils.exec_cmd("ssh " + benchbase_ip + " \"cd " + benchbase_dir + " ; " + java_cmd + "\"")
                print("Finish config - { " + result_file + " }")
            else:
                print("Run config - { " + result_file + " }")
                result_file = unique_ts + "_" + result_file
                java_cmd = "java -jar benchbase.jar -b ycsb -c " + dir_name + os.path.basename(
                    conf_file) + " --execute=true -d " + result_file
                target1 = lambda: utils.exec_cmd("ssh " + benchbase_ip + " \"cd " + benchbase_dir + " ; " + java_cmd + "\"")
                target2 = lambda: utils.exec_cmd("./set_delay.py -s dynamic")
                thread1 = threading.Thread(target=target1)
                thread2 = threading.Thread(target=target2)
                thread1.start()
                thread2.start()
                thread1.join()
                thread2.join()
                print("Finish config - { " + result_file + " }")
            time.sleep(5)
    elif args.wl == "tpcc":
        # traverse the dir
        local_dir_name = "../config/tpcc_" + f + "/"
        dir_name = "config/" + args.engine + "/tpcc_" + f + "/"
        for conf_file in utils.traverse_dir(local_dir_name):
            result_file = "result/" + os.path.splitext(os.path.basename(conf_file))[0]
            print("Run config - { " + result_file + " }")
            java_cmd = "java -jar benchbase.jar -b tpcc -c " + dir_name + os.path.basename(
                conf_file) + " --execute=true -d " + result_file
            utils.exec_cmd("ssh " + benchbase_ip + " \"cd " + benchbase_dir + " ; " + java_cmd + "\"")

            print("Finish config - { " + result_file + " }")
            time.sleep(5)
        pass

    # 4.2 scp results into local dir
    unique_ts = datetime.now().strftime('%Y%m%d%H%M%S')
    result_path = "/data/geotrx-results/" + s + "/" + args.wl + "_" + f + "/" + a + "/" + f + "_" + unique_ts
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    utils.exec_cmd("scp -r root@" + benchbase_ip + ":" + benchbase_dir + "/results/* " + result_path)

    # 4.3 delete remote directory
    remote_result_dir = benchbase_path + "/benchbase-" + args.engine + "/results"
    # utils.exec_cmd("ssh " + benchbase_ip + " \"cd " + remote_result_dir + " ; " + "rm -rf *\"")
    utils.exec_cmd("ssh " + benchbase_ip + " \"rm -rf " + remote_result_dir + "\"")

    # 5. close shardingsphere
    utils.exec_cmd("bash " + ssp_path + "stop.sh")
    utils.exec_cmd("rm -rf /home/geotrx/shardingsphere/distribution/proxy/target/apache-shardingsphere-5.3.3-SNAPSHOT"
                   "-shardingsphere-proxy-bin/logs")

    # 6. close benchbase
    exec_cmd = "ps -ef | grep benchbase | grep -v grep | awk '{print $2}' | xargs kill -9"
    utils.exec_cmd("ssh " + benchbase_ip + " \" " + exec_cmd + "\"")

    # 7. close agent
    for ds_ip in datasource_ip:
        exec_cmd = "ps -ef | grep sspagent | grep -v grep | awk '{print $2}' | xargs kill -9"
        utils.exec_cmd("ssh " + ds_ip + " \" " + exec_cmd + "\"")

    # 8. rollback xa transactions if exists
    exec_cmd = "java -classpath /data/XARecoverProject/target/classes:/root/.m2/repository/com/mysql/mysql-connector" \
               "-j/8.0.31/mysql-connector-j-8.0.31.jar:/root/.m2/repository/com/google/protobuf/protobuf-java/3.19.4" \
               "/protobuf-java-3.19.4.jar:/root/.m2/repository/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar" \
               ":/root/.m2/repository/org/checkerframework/checker-qual/3.31.0/checker-qual-3.31.0.jar " \
               "org.dbiir.harp.Main"
    utils.exec_cmd(exec_cmd)

    utils.exec_cmd("./unset_delay.py")
    time.sleep(5)


def run_cnt(s: str, a: str, f: str, cnt: int):
    for i in range(cnt):
        run_once(s, a, f)


if __name__ == "__main__":
    args = parse_args()
    start_time = datetime.now()
    print("workload: " + args.wl + " engine: " + args.engine)
    ss, aa, ff = scenarios, algorithms, functions
    if args.scenario is not None:
        ss = args.scenario
    if args.alg is not None:
        aa = args.alg
    if args.func is not None:
        ff = args.func
    all_combinations = list(product(ss, aa, ff))

    for s, a, f in all_combinations:
        # 1. choose scenario to set delay
        if s == "country_emu" or s == "city_emu":
            run_cnt(s, a, f, 5)
        if s == "dynamic":
            run_cnt(s, a, f, 2)
        else:
            run_once(s, a, f)

    print("start time: ", start_time)
    print("end time: ", datetime.now())
