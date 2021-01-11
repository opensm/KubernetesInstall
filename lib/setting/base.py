# -*- coding: utf-8 -*-
from lib.settings import CURRENT_PATH, INSTALL_ROOT
import os

# 以下为目录定义
# ######################临时安装主目录##############################
TMP_PACKAGE_PATH = os.path.join(CURRENT_PATH, 'package')
TMP_ROOT_DIR = os.path.join(CURRENT_PATH, 'package')
# #临时安装脚本目录
TMP_SYSTEMCTL_DIR = os.path.join(CURRENT_PATH, 'systemctl')
CMD_FILE_DIR = os.path.join(CURRENT_PATH, 'exec')
TAG_FILE_DIR = os.path.join(CURRENT_PATH, 'tmp')
YAML_FILE_DIR = os.path.join(CURRENT_PATH, 'yaml')
SYSTEMCTL_DIR = '/usr/lib/systemd/system'

CLUSTER_DNS = '10.96.0.10'
DNS_IP = [CLUSTER_DNS]
CLUSTER_ADDRESS = '10.244.0.0/16'
SERVICE_CLUSTER_IP_RANGE = "10.96.0.0/12"
SERVICE_NODE_PORT_RANGE = "30000-32767"
KUBE_APISERVER_SECURE_PORT = 6443

IMAGE_DICT = {
    "pause": "pause:3.1",
    "CNI": 'flannel:v0.13.1-rc1',
    "coredns": "coredns:1.4.0"
}

KUBERNETES_MASTER_PACKAGE = os.path.join(
    TMP_PACKAGE_PATH, 'kubernetes-server-linux-amd64.tar.gz'
)
KUBERNETES_NODE_PACKAGE = os.path.join(
    TMP_PACKAGE_PATH, 'kubernetes-node-linux-amd64.tar.gz'
)

# cni版本
CNI_VERSION = "0.8.6"
CNI_PACKAGE = "cni-plugins-linux-amd64-v{0}.tgz".format(CNI_VERSION)
ABS_CNI_PACKAGE = os.path.join(
    TMP_PACKAGE_PATH,
    CNI_PACKAGE
)
# etcd 临时安装目录
ETCD_VERSION = "v3.4.9"
ETCD_PACKAGE = "etcd-{0}-linux-amd64.tar.gz".format(ETCD_VERSION)
ABS_ETCD_PACKAGE = os.path.join(TMP_PACKAGE_PATH, ETCD_PACKAGE)

PACKAGE_LIST = {
    KUBERNETES_NODE_PACKAGE,
    KUBERNETES_MASTER_PACKAGE,
    ABS_CNI_PACKAGE,
    ABS_ETCD_PACKAGE
}
__all__ = [
    'TMP_PACKAGE_PATH',
    'TMP_SYSTEMCTL_DIR',
    'CMD_FILE_DIR',
    'TAG_FILE_DIR',
    'YAML_FILE_DIR',
    'SYSTEMCTL_DIR',
    'DNS_IP',
    'CLUSTER_ADDRESS',
    'SERVICE_CLUSTER_IP_RANGE',
    'SERVICE_NODE_PORT_RANGE',
    'KUBE_APISERVER_SECURE_PORT',
    'IMAGE_DICT',
    'INSTALL_ROOT',
    'PACKAGE_LIST',
    'KUBERNETES_MASTER_PACKAGE',
    'KUBERNETES_NODE_PACKAGE',
    'CNI_VERSION',
    'CNI_PACKAGE',
    'ABS_CNI_PACKAGE',
    'ABS_ETCD_PACKAGE',
    'ETCD_PACKAGE',
    'ETCD_VERSION',
    'TMP_ROOT_DIR',
    'CLUSTER_DNS'
]
