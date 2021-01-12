# -*- coding: utf-8 -*-
from lib.KubeInstall import KubernetesInstall
from lib.OpenSSlControl import OpenSSLControl
from lib.EtcdInstall import EtcdInstall
from lib.Haproxy import HaProxyInstall
from lib.CniInstall import CNIInstall
from lib.Keepalived import KeepalivedInstall
from lib.FileCommand import AchieveControl
from lib.dependent import *
from lib.settings import *
import sys

# 声明类
k = KubernetesInstall()
s = OpenSSLControl()
e = EtcdInstall()
h = HaProxyInstall()
c = CNIInstall()
kp = KeepalivedInstall()
a = AchieveControl()

check_file = os.path.join(CURRENT_PATH, 'tmp', 'install.lock')
if os.path.exists(check_file):
    print("已完成安装，请确认是否可以重复执行！")
    sys.exit(1)
# 检查变量
check_env()
# 全局依赖安装
# 测试
dependent()
kernel_update()
docker_install()
# openssl 证书
s.run_openssl()
# etcd 安装并启动
e.run_etcd()
# kubernetes 安装
k.package_decompression()
# 生成kubernetes代码和配置同步
k.kubernetes_rsync()
if len(KUBERNETES_MASTER.values()) > 1:
    # HA安装、启动
    h.run_haproxy()
    # Keepalived安装、启动
    kp.run_keepalive()
# CNI安装
c.run_cni()
# 生成验证秘钥
k.bootstrappers_install()
k.write_flannel_yaml()
k.write_coredns_yaml()
# kube_proxy config 同步
k.kube_proxy_rsync()
a.touch_achieve(achieve=check_file)
