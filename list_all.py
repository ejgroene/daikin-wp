#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sensor_lib import parse_response, http_get, get_time, power_2_energy, get_time_and_energy
from time import sleep
from itertools import chain

from sys import argv
ip_addr = argv[1]

requests = ['common/basic_info', 'common/get_remote_method', 'aircon/get_model_info', 'aircon/get_sensor_info', 'aircon/get_target', 'aircon/get_week_power', 'aircon/get_year_power', 'aircon/get_program', 'aircon/get_scdltimer', 'common/get_notify']

def get_all(ip_addr):
    return dict(chain.from_iterable(http_get(ip_addr, r).items() for r in requests))

parms0 = get_all(ip_addr)
print("*** Initial values ***")
for k, v in parms0.items():
    print("{:<30}{:<}".format(k, v))

print("*** Tracking changes ***")
while True:
    parms1 = get_all(ip_addr)
    for k, v in parms1.items():
        if v != parms0[k]:
            print("{:<30}{:<}".format(k, v))
    parms0 = parms1
    sleep(60)
