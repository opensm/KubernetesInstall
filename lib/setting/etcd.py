# -*- coding: utf-8 -*-
from lib.settings import INSTALL_ROOT
from lib.setting.base import TMP_ROOT_DIR, ETCD_PACKAGE, ABS_ETCD_PACKAGE
import os

# #etcd 临时安装目录
TMP_ETCD_DIR = os.path.join(TMP_ROOT_DIR, ETCD_PACKAGE.replace('.tar.gz', ''))
TMP_ETCD_BIN_DIR = os.path.join(TMP_ETCD_DIR, 'bin')
TMP_ETCD_CONFIG_DIR = os.path.join(TMP_ETCD_DIR, 'conf')
TMP_ETCD_SSL_DIR = os.path.join(TMP_ETCD_DIR, 'ssl')

# 环境变量 etcd 安装目录
ETCD_HOME = os.path.join(INSTALL_ROOT, "etcd")
ETCD_CONFIG_DIR = os.path.join(ETCD_HOME, "conf")
ETCD_SSL_DIR = os.path.join(ETCD_HOME, "ssl")
ETCD_BIN_DIR = os.path.join(ETCD_HOME, "bin")

ETCD_SSL_LIST = [
    "ca.crt", "ca.key", "ca.srl", "healthcheck-client.crt",
    "healthcheck-client.csr", "healthcheck-client.key", "peer.crt",
    "peer.csr", "peer.key", "server.crt", "server.csr", "server.key"
]

ETCD_CONFIG_DICT = {
    "data-dir": "/data/etcd/data",
    "wal-dir": "/data/etcd/wal",
    "snapshot-count": 5000,
    "heartbeat-interval": 100,
    "election-timeout": 1000,
    "quota-backend-bytes": 0,
    "max-snapshots": 3,
    "max-wals": 5,
    "initial-cluster-token": 'etcd-k8s-cluster',
    "initial-cluster-state": 'new',
    "strict-reconfig-check": False,
    "enable-v2": True,
    "enable-pprof": True,
    "proxy": 'off',
    "proxy-failure-wait": 5000,
    "proxy-refresh-interval": 30000,
    "proxy-dial-timeout": 1000,
    "proxy-write-timeout": 5000,
    "proxy-read-timeout": 0,
    "debug": False,
    "logger": "zap",
    "force-new-cluster": False,
    "client-transport-security": {
        "ca-file": os.path.join(ETCD_SSL_DIR, "ca.crt"),
        "cert-file": os.path.join(ETCD_SSL_DIR, "server.crt"),
        "key-file": os.path.join(ETCD_SSL_DIR, "server.key"),
        "client-cert-auth": False,
        "trusted-ca-file": os.path.join(ETCD_SSL_DIR, "ca.crt"),
        "auto-tls": False
    },
    "peer-transport-security": {
        "ca-file": os.path.join(ETCD_SSL_DIR, "ca.crt"),
        "cert-file": os.path.join(ETCD_SSL_DIR, "peer.crt"),
        "key-file": os.path.join(ETCD_SSL_DIR, "peer.key"),
        "peer-client-cert-auth": False,
        "trusted-ca-file": os.path.join(ETCD_SSL_DIR, "ca.crt"),
        "auto-tls": False
    }
}
