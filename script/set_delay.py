#!/usr/bin/python3
import random
import subprocess
import argparse
import time

import utils
import os

benchbase_ip = "11.127.237.44"
ds_ip = ["11.99.55.8", "11.99.55.9", "11.99.55.12", "11.129.111.12"]
ssp_ip = ["11.129.108.223"]
interface = "bond1"
scenarios = ['back_0', 'back_1', 'back_2', 'normal', 'country_emu', 'city_emu', 'dynamic', "variance1",
             'variance2', "variance3", 'variance4', 'variance5', 'variance6', 'variance7', 'variance8', 'variance9']


def del_delay():
    cmd = "tc qdisc del root dev " + interface + " 2>/dev/null"
    utils.exec_cmd(cmd)


def create_class():
    cmd = "tc qdisc add dev " + interface + " root handle 1:0 htb"
    utils.exec_cmd(cmd)


def add_delay(ip: str, group_id: int, delay: float):
    cmd1 = "tc filter add dev " + interface + " parent 1:0 prior 2 protocol ip u32 match ip dst " + ip + " classid 1:" + \
           str(group_id)
    utils.exec_cmd(cmd1)
    cmd2 = "tc class add dev " + interface + " parent 1:0 classid 1:" + str(group_id) + " htb rate 10Gbit"
    utils.exec_cmd(cmd2)
    cmd3 = "tc qdisc add dev " + interface + " parent 1:" + str(group_id) + " handle " + str(group_id + 1) \
           + ":0 netem delay " + str(delay) + "ms"
    utils.exec_cmd(cmd3)


def back_0():
    # set 11.99.55.12 to 30ms
    del_delay()
    create_class()
    for i in range(len(ds_ip)):
        add_delay(ds_ip[i], i + 1, 10)


def back_1():
    # set 11.99.55.12 to 30ms
    del_delay()
    create_class()
    for i in range(len(ds_ip)):
        if ds_ip[i] == "11.99.55.12":
            add_delay(ds_ip[i], i + 1, 30)
        else:
            add_delay(ds_ip[i], i + 1, 10)


def back_2():
    # set 11.99.55.12 and 11.129.111.12 to 30ms and 100ms
    del_delay()
    create_class()
    for i in range(len(ds_ip)):
        if ds_ip[i] == "11.129.111.12":
            add_delay(ds_ip[i], i + 1, 100)
        elif ds_ip[i] == "11.99.55.12":
            add_delay(ds_ip[i], i + 1, 30)
        else:
            add_delay(ds_ip[i], i + 1, 10)


def normal():
    del_delay()
    create_class()
    for i in range(len(ds_ip)):
        if ds_ip[i] == "11.99.55.9":
            add_delay(ds_ip[i], i + 1, 27)
        elif ds_ip[i] == "11.99.55.12":
            add_delay(ds_ip[i], i + 1, 73)
        elif ds_ip[i] == "11.129.111.12":
            add_delay(ds_ip[i], i + 1, 251)


def country_emu():
    del_delay()
    create_class()
    latencies = country_rand(len(ds_ip))

    for i in range(len(ds_ip)):
        if ds_ip[i] == "11.99.55.8":
            continue
        else:
            add_delay(ds_ip[i], i + 1, latencies[i])


def city_emu():
    del_delay()
    create_class()
    latencies = city_rand(len(ds_ip))

    for i in range(len(ds_ip)):
        if ds_ip[i] == "11.99.55.8":
            continue
        else:
            add_delay(ds_ip[i], i + 1, latencies[i])


def country_rand(cnt: int):
    # 模拟跨国链路间的网络时延 [100, 300)
    res = []
    for i in range(cnt):
        res.append(random.random() * 200 + 100)

    return res


def city_rand(cnt: int):
    # 模拟跨国链路间的网络时延 [30, 100)
    res = []
    for i in range(cnt):
        res.append(random.random() * 70 + 30)

    return res


def template_latency(delay1, delay2, delay3, delay4):
    del_delay()
    create_class()
    add_delay("11.99.55.8", 1, delay1)
    add_delay("11.99.55.9", 2, delay2)
    add_delay("11.99.55.12", 3, delay3)
    add_delay("11.129.111.12", 4, delay4)


def dynamic():
    template_latency(0, 10, 10, 10)
    time.sleep(40)
    template_latency(0, 50, 90, 170)
    time.sleep(20)
    template_latency(0, 50, 50, 90)
    time.sleep(20)
    template_latency(0, 10, 10, 10)
    time.sleep(20)
    template_latency(0, 10, 10, 50)
    time.sleep(20)
    template_latency(0, 50, 90, 250)
    time.sleep(20)
    template_latency(0, 10, 50, 90)
    time.sleep(20)
    template_latency(0, 10, 10, 10)
    time.sleep(20)


def variance1(times: int):
    # average is 20 ms
    template_latency(0 * times, 20 * times, 20 * times, 20 * times)


def variance2(times: int):
    template_latency(0 * times, 10 * times, 20 * times, 30 * times)
    pass


def variance3(times: int):
    template_latency(0 * times, 10 * times, 20 * times, 30 * times)
    pass


def variance4(times: int):
    template_latency(0 * times, 0 * times, 20 * times, 40 * times)
    pass


def variance5(times: int):
    template_latency(0 * times, 0 * times, 20 * times, 40 * times)
    pass


def variance6(times: int):
    template_latency(0 * times, 0 * times, 15 * times, 45 * times)


def variance7(times: int):
    template_latency(0 * times, 0 * times, 10 * times, 50 * times)


def variance8(times: int):
    # average is 100 ms
    template_latency(0 * times, 0 * times, 5 * times, 55 * times)


def variance9(times: int):
    template_latency(0 * times, 0 * times, 0 * times, 60 * times)


functions = {
    "back_0": back_0,
    "back_1": back_1,
    "back_2": back_2,
    "normal": normal,
    "country_emu": country_emu,
    "city_emu": city_emu,
    "dynamic": dynamic,
    "variance1": variance1,
    "variance2": variance2,
    "variance3": variance3,
    "variance4": variance4,
    "variance5": variance5,
    "variance6": variance6,
    "variance7": variance7,
    "variance8": variance8,
    "variance9": variance9,
}


if __name__ == "__main__":
    print("========== set delay begin ==========")
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scenario", choices=scenarios, dest='scenario', type=str, nargs='+', required=True,
                        help="specify the simulation scenario")
    parser.add_argument("-t", "--times", dest='times', type=int, nargs=1, required=False, default=1,
                        help="specify the simulation scenario")
    args = parser.parse_args()
    # assert (len(args.scenario) == 1)

    print("scenario: " + args.scenario[0])

    if args.times is not 1:
        assert args.scenario[0].__contains__("variance")
        functions.get(args.scenario[0])(args.times[0])
    else:
        functions.get(args.scenario[0])()
    print("========== set delay finish ==========")
