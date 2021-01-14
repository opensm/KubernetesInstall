# Kubernetes 一键安装工具
## 说明:
`脚本中不包含
1.kubernetes-node-linux-amd64.tar.gz  
2.kubernetes-server-linux-amd64.tar.gz  
请将以上文件下载并放置到
`
[lib/package](https://github.com/opensm/KubernetesInstall/tree/main/lib/package)

## 版本：
`kubernetes:v1.8    
Etcd:3.4.9         
Cni:0.8.6         
flannel/cni:v3.9.6   
coredns:1.4.0   `
## _安装步骤_
### 1. 配置文件修改 
#### 文件：lib/setting.py
```
# 网卡名称
IFNAME = 'ens33'
# 主机用于同步和安装的账号密码 //集群所有主机密码必须一致//
AUTHENTICATION = {
    'user': 'root',
    'passwd': '123456',
    'port': 22
}
# k8s API信息 master单节点请填写master地址，多节点请填写VIP
KUBERNETES_VIP = "192.168.174.11"
KUBERNETES_PORT = 8443
KUBERNETES_APISERVER = "https://{0}:{1}".format(KUBERNETES_VIP, KUBERNETES_PORT)
# LOG自定义参数 DEBUG打印详细信息
LOG_LEVEL = "INFO"
LOG_DIR = "/tmp"
LOG_FILE = "install.log"

# etcd 节点定义
ETCD_CLUSTER_LIST = ["192.168.174.8", "192.168.174.9", "192.168.174.10"]
# etcd节点前缀
ETCD_PREFIX = "etcd"
# kuberneters节点定义
KUBERNETES_MASTER = {
    "master01": "192.168.174.8"
}
KUBERNETES_NODE = {
    "node01": "192.168.174.9",
    "node02": "192.168.174.10"
}
```
### 2. 执行依赖安装
#### bash dependent.sh
### 3. 执行安装
#### python run.py
### 4. 确认重启之后进入脚本目录继续执行
#### python run.py
##  _支持环境_
### 系统：Centos 7 
### python版本：python2.7
### CPU: 2核以上
### 内存: 不低于4G
###脚本将持续更新 有问题请联系我 QQ:1096010121
