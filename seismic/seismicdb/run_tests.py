#!/usr/bin/env python3
import obspy
import msgpack
import requests
from iso8601 import parse_date
from os import listdir, path


def upload(filename):
    s = obspy.read(filename)
    t = s[0]

    tags = {
        'network': t.meta.network,
        'station': t.meta.station,
        'channel': t.meta.channel[-1:],
        'sampling_rate': t.meta.sampling_rate,
    }

    test_payload = {
        'tags': tags,
        'start': parse_date(str(t.meta.starttime)).replace(tzinfo=None).timestamp() * 1000,
        'end': parse_date(str(t.meta.endtime)).replace(tzinfo=None).timestamp() * 1000,
        'interval': 1000 / t.meta.sampling_rate,
        'datapoints': t.data.tolist(),
    }

    m = msgpack.packb(test_payload, use_bin_type=True)

    r = requests.put("http://localhost:5000/v1/metrics", data=m, headers={'Content-Type': "application/msgpack"})
    if r.status_code >= 400:
        print(r.content)


directories = ['/srv/seismic_raw/2011.239/', '/srv/seismic_raw/2011.240/', '/srv/seismic_raw/2011.241/']
for d in directories:
    for f in listdir(d):
        if '00.00.00' in f:
            upload(path.join(d, f))