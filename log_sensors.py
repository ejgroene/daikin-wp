#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sensor_lib import http_get, get_time_and_energy
from time import sleep
from sys import argv

OUTDOOR_LABELS = [u'T-out [ºC]', 'Freq [Hz]', 'Zon [Wm2]']
INDOOR_LABELS = [u'T-{0} [ºC]', 'E-{0} [kWh]']

OUTDOOR_SENSORS = ['{otemp}', '{cmpfreq}', '{zon}']
INDOOR_SENSORS = ['{htemp}', '{energy}']

assert len(OUTDOOR_SENSORS) == len(OUTDOOR_LABELS)
assert len(INDOOR_SENSORS) == len(INDOOR_LABELS)

interval = int(argv[1])
ip_addresses = argv[2:]

unit_info = [http_get(ip_addr, "common/basic_info") for ip_addr in ip_addresses]
unit_names = [info['name'] for info in unit_info]
print "Units:", ', '.join(unit_names)

filename = "all_sensor_data.csv"
print "Logging to:", filename

header = ['Date'] + OUTDOOR_LABELS
for name in unit_names:
    header += [label.format(name) for label in INDOOR_LABELS]

def zon():
    try:
        api = "https://api.buienradar.nl"
        from urllib2 import urlopen
        response = urlopen(api).read()
        arnhem = response.split('<weerstation id="6275">')[1].split('</weerstation>')[0]
        zon_intensiteit = arnhem.split('<zonintensiteitWM2>')[1].split('</zonintensiteitWM2>')[0]
    except Exception, e:
        print e
        zon_intensiteit = "-1"
    return int(zon_intensiteit)

with open(filename, "a") as f:
    if f.tell() == 0:
        f.write(u', '.join(header).encode('utf-8') + '\r\n')

    while True:
        try:
            time_energy = [get_time_and_energy(ip_addr) for ip_addr in ip_addresses]
            timestamp = time_energy[0][0]
            indoor_data = [http_get(ip_addr, 'aircon/get_sensor_info') for ip_addr in ip_addresses]
            indoor_data = [dict(d, energy=te[1]) for d, te in zip(indoor_data, time_energy)]
            outdoor_data = indoor_data[0]
            outdoor_data['zon'] = zon()

            line = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]
            line += [sensor.format(**outdoor_data) for sensor in OUTDOOR_SENSORS]
            for data in indoor_data:
                line += [sensor.format(**data) for sensor in INDOOR_SENSORS]

        except Exception, e:
            print e
        else:
            f.write(', '.join(line) + '\r\n')
            f.flush()
        sleep(interval)

