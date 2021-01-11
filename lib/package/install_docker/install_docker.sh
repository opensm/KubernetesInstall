#!/bin/bash

DIR=$(
  # shellcheck disable=SC2046
  # shellcheck disable=SC2164
  cd $(dirname "$0")
  pwd
)

yum -y remove docker \
docker-client \
docker-client-latest \
docker-common \
docker-latest \
docker-latest-logrotate \
docker-logrotate \
docker-engine \
keepalived \
haproxy
tar xzfv "$DIR"/docker/docker.tgz -C "$DIR"/docker/
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
  echo "解压文件失败！$DIR/docker/docker.tgz"
  exit 1
fi
cp -arf "$DIR"/docker/docker/* /usr/local/bin/
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<EOF
{
    "log-driver": "json-file",
    "exec-opts": ["native.cgroupdriver=cgroupfs"],
    "log-opts": {
    "max-size": "100m",
    "max-file": "3"
    },
    "live-restore": true,
    "max-concurrent-downloads": 10,
    "max-concurrent-uploads": 10,
    "registry-mirrors": ["https://2lefsjdg.mirror.aliyuncs.com"],
    "storage-driver": "overlay2",
    "storage-opts": [
    "overlay2.override_kernel_check=true"
    ]
}
EOF
cat >/usr/lib/systemd/system/docker.service <<EOF
[Unit]

Description=Docker Application Container Engine

Documentation=https://docs.docker.com

After=network-online.target firewalld.service

Wants=network-online.target


[Service]

Type=notify

# the default is not to use systemd for cgroups because the delegate issues still

# exists and systemd currently does not support the cgroup feature set required

# for containers run by docker

ExecStart=/usr/local/bin/dockerd

ExecReload=/bin/kill -s HUP $MAINPID

# Having non-zero Limit*s causes performance problems due to accounting overhead

# in the kernel. We recommend using cgroups to do container-local accounting.

LimitNOFILE=infinity

LimitNPROC=infinity

LimitCORE=infinity

# Uncomment TasksMax if your systemd version supports it.

# Only systemd 226 and above support this version.

#TasksMax=infinity

TimeoutStartSec=0

# set delegate yes so that systemd does not reset the cgroups of docker containers

Delegate=yes

# kill only the docker process, not all processes in the cgroup

KillMode=process

# restart the docker process if it exits prematurely

Restart=on-failure

StartLimitBurst=3

StartLimitInterval=60s


[Install]

WantedBy=multi-user.target
EOF
echo "------start docker------"
systemctl daemon-reload
systemctl start docker
systemctl enable docker
# shellcheck disable=SC2181
if [ $? -eq 0 ]; then
  docker load <"$DIR"/images/pause.tar.gz
  docker load <"$DIR"/images/busybox.tar.gz
  docker load <"$DIR"/images/coredns.tar.gz
  docker load <"$DIR"/images/flannel.tar.gz

  docker tag c7c37e472d31 busybox:latest
  docker tag a9e015907f63 coredns:1.4.0
  docker tag da86e6ba6ca1 pause:3.1
  docker tag f03a23d55e57 flannel:v0.13.1-rc1

else
  exit 1
fi
docker -v
exit 0
