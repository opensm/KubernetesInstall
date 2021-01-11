# -*- coding: utf-8 -*-
from lib.setting.openssl import *

INSTALL_ROOT = "/usr/local"
CURRENT_PATH = os.path.split(os.path.realpath(__file__))[0]

# 获取IP的网卡名称
IFNAME = 'ens33'
# 主机的用户名密码
AUTHENTICATION = {
    'user': 'root',
    'passwd': '123456',
    'port': 22
}

# LOG自定义参数
LOG_LEVEL = "DEBUG"
LOG_DIR = "/tmp"
LOG_FILE = "install.log"

# etcd 节点定义
ETCD_CLUSTER_LIST = ["192.168.174.11", "192.168.174.12", "192.168.174.13"]
ETCD_PREFIX = "etcd"
# kuberneters节点定义
KUBERNETES_MASTER = {
    "master01": "192.168.174.11"
}
KUBERNETES_NODE = {
    "node01": "192.168.174.12",
    "node02": "192.168.174.13"
}
if len(KUBERNETES_MASTER.values()) == 1:
    KUBERNETES_PORT = 6443
elif len(KUBERNETES_MASTER.values()) > 1:
    KUBERNETES_PORT = 8443
else:
    raise Exception('Master节点个数异常！')

# k8s API信息
KUBERNETES_VIP = "192.168.174.11"
KUBERNETES_APISERVER = "https://{0}:{1}".format(KUBERNETES_VIP, KUBERNETES_PORT)
# 远程临时拷贝目录
REMOTE_TMP_DIR = '/opt/tmp'
