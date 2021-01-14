#!/bin/bash

###关闭selinux，关闭防火墙，升级内核，关闭swap，开启内核转发参数，开启IPVS，安装docker##

#报错退出
set -e

SELINUX_STATUS=$(getenforce)
#关闭防火墙
systemctl stop firewalld && systemctl disable firewalld

echo "所有节点关闭selinux和firewalld"
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
if [ "$SELINUX_STATUS" == 'Disabled' ]; then
  echo "selinux already diabled"
else
  setenforce 0
fi

##所有节点关闭swap
cat >>/etc/sysctl.d/swap.conf <<EOF
vm.swappiness = 0
EOF

sysctl -p
swapoff -a
sed -ri 's/.*swap.*/#&/' /etc/fstab

##开启内核转发参数
cat <<EOF >/etc/sysctl.d/k8s.conf
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 10
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
net.ipv4.neigh.default.gc_stale_time = 120
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.default.arp_announce = 2
net.ipv4.conf.lo.arp_announce = 2
net.ipv4.conf.all.arp_announce = 2
net.ipv4.ip_forward = 1
net.ipv4.tcp_max_tw_buckets = 5000
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_synack_retries = 2
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.netfilter.nf_conntrack_max = 2310720
fs.inotify.max_user_watches=89100
fs.may_detach_mounts = 1
fs.file-max = 52706963
fs.nr_open = 52706963
net.bridge.bridge-nf-call-arptables = 1
vm.swappiness = 0
vm.overcommit_memory=1
vm.panic_on_oom=0
EOF

sysctl -p

yum -y install conntrack-tools libnl-devel.x86_64
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo "conntrack-tools 安装失败"
fi
echo "-----please reboot-----"
exit 0
