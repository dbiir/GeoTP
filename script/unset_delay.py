#!/usr/bin/python3
import random
import subprocess
import argparse
import utils
import os

benchbase_ip = "11.127.237.44"
ds_ip = ["11.99.55.8", "11.99.55.9", "11.99.55.12", "11.129.111.12"]
ssp_ip = ["11.129.108.223"]
interface = "bond1"


def del_delay():
    cmd = "tc qdisc del root dev " + interface + " 2>/dev/null"
    utils.exec_cmd(cmd)


if __name__ == "__main__":
    print("========== unset delay begin ==========")
    del_delay()
    print("========== unset delay finish ==========")
