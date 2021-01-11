#!/bin/bash

yum -y install libnl libnl-devel libnfnetlink-devel wget openssl openssl-devel gcc-c++ vim -y
python get-pip.py
pip install -r requirements.txt
