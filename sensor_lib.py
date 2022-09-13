#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.request import urlopen, unquote
from datetime import datetime
from time import sleep

## code ##

def parse_response(response, *keys):
    return {unquote(k): unquote(v)
                for (k,v) in (kv.split(b'=')
                    for kv in response.split(b','))
                if not keys or unquote(k) in keys}

def http_get(ip_addr, path, *keys):
    response = urlopen("http://%s/%s" % (ip_addr, path)).read()
    return parse_response(response, *keys)

def get_time(ip_addr):
    t = http_get(ip_addr, 'common/get_datetime', 'cur')['cur'] #2016/7/7 21:23:28
    return datetime.strptime(t, "%Y/%m/%d %H:%M:%S")

def get_power(ip_addr):
    return http_get(ip_addr, "aircon/get_day_power_ex?days=1", 'curr_day_heat')['curr_day_heat']

def power_2_energy(daikin_powers, t1):
    return sum(float(p100W)/10 for p100W in daikin_powers.split('/')[:t1.hour])

def get_time_and_energy(ip_addr):
    # Daikin completely fails to produce a sensible discrete time signal of power or energy.
    # The signal does not exist for many sample times. Or duplicates if you sample out of step
    # with when Daikin thinks it is time to start en new interval.
    # Hence operations like differentiating, averaging, etc become next to impossible.
    # We fix this by integrating the given array of hourly 100 Wh unit of consumption over the
    # hourly time buckets that Daikin uses.
    # For that we must first relate the Daikin data to the correct time, which we do by checking twice.
    # Next we integrate to just before the given hour, as the current hour might still change.
    # This results in a monotonic discrete time signal which resets every day, which is easy to
    # fix because it is monotonic. 
    t0 = get_time(ip_addr)
    daikin_powers = get_power(ip_addr)
    t1 = get_time(ip_addr)
    # check if the clock changed day in between
    if t0.date() != t1.date():
        daikin_powers = get_power(ip_addr)
    # we integrate the power as to make it a continuous discrete signal again (daikin screws up)
    E = power_2_energy(daikin_powers, t1)
    return t1, E



## test ##

INFO_RESPONSE = b"ret=OK,type=aircon,reg=eu,dst=1,ver=3_3_1,pow=0,err=0,location=0,name=%77%65%72%6b%70%6c%61%61%74%73,icon=5,method=home only,port=30051,id=,pw=,lpw_flag=0,adp_kind=2,pv=3.20,cpv=3,cpv_minor=20,led=1,en_setzone=1,mac=A0CC2BD73D31,adp_mode=run,en_hol=0,grp_name=,en_grp=0"

info = parse_response(INFO_RESPONSE)
assert info == {'pow': '0', 'grp_name': '', 'port': '30051', 'adp_kind': '2', 'ver': '3_3_1', 'pw': '', 'dst': '1', 'ret': 'OK', 'id': '', 'en_setzone': '1', 'location': '0', 'en_grp': '0', 'cpv_minor': '20', 'en_hol': '0', 'type': 'aircon', 'method': 'home only', 'led': '1', 'mac': 'A0CC2BD73D31', 'lpw_flag': '0', 'pv': '3.20', 'icon': '5', 'name': 'werkplaats', 'err': '0', 'adp_mode': 'run', 'reg': 'eu', 'cpv': '3'}, info

info = parse_response(INFO_RESPONSE, 'name', 'mac')
assert info == {'name': 'werkplaats', 'mac': 'A0CC2BD73D31'}, info


POWER_RESPONSE = b"ret=OK,curr_day_heat=0/0/0/0/0/0/0/0/0/0/0/3/2/2/3/0/0/0/0/0/0/0/0/0,prev_1day_heat=0/0/0/0/0/0/0/0/0/0/0/6/6/6/5/0/0/0/0/0/0/0/0/0,prev_2day_heat=4/5/4/4/5/4/5/4/5/5/4/5/4/3/4/2/2/2/0/0/0/0/0/0,prev_3day_heat=4/4/4/3/3/4/3/4/3/5/4/5/4/3/3/2/2/2/3/4/3/3/4/5,prev_4day_heat=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/2/3/3/4/3,prev_5day_heat=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_6day_heat=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,curr_day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_1day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_2day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_3day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_4day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_5day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0,prev_6day_cool=0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0/0"

powers = parse_response(POWER_RESPONSE, 'curr_day_heat')['curr_day_heat']
assert powers == "0/0/0/0/0/0/0/0/0/0/0/3/2/2/3/0/0/0/0/0/0/0/0/0"
assert power_2_energy(powers, datetime(1900, 12, 31, 10)) == 0
assert power_2_energy(powers, datetime(1900, 12, 31, 11)) == 0
assert power_2_energy(powers, datetime(1900, 12, 31, 12)) == 0.3
assert power_2_energy(powers, datetime(1900, 12, 31, 13)) == 0.5
assert power_2_energy(powers, datetime(1900, 12, 31, 14)) == 0.7
assert power_2_energy(powers, datetime(1900, 12, 31, 15)) == 1.0
#                               11     15 
powers = "0/0/0/0/0/0/0/0/0/0/0/3/2/2/3/9/0/0/0/0/0/0/0/0"
assert power_2_energy(powers, datetime(1900, 12, 31, 15)) == 1.0
assert power_2_energy(powers, datetime(1900, 12, 31, 16)) == 1.9


SENSOR_RESPONSE = b"ret=OK,htemp=23.0,hhum=-,otemp=16.0,err=10000,cmpfreq=16"

assert parse_response(SENSOR_RESPONSE) == {'otemp': '16.0', 'hhum': '-', 'err': '10000', 'cmpfreq': '16', 'ret': 'OK', 'htemp': '23.0'}
