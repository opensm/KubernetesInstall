# -*- coding: utf-8 -*-
import os
import random
import string
from lib.settings import KUBERNETES_MASTER, ETCD_CLUSTER_LIST
from lib.setting.base import *
from lib.setting.cni import CNI_BIN_DIR, CNI_CONFIG_DIR

# 环境变量

# #kubernetes 临时安装目录
TMP_KUBERNETES_HOME_DIR = os.path.join(TMP_ROOT_DIR, 'kubernetes')
# ##master节点临时安装目录
TMP_KUBERNETES_MASTER_DIR = os.path.join(TMP_KUBERNETES_HOME_DIR, 'server')
TMP_KUBERNETES_MASTER_BIN_DIR = os.path.join(TMP_KUBERNETES_MASTER_DIR, 'bin')
TMP_KUBERNETES_MASTER_CONFIG_DIR = os.path.join(TMP_KUBERNETES_MASTER_DIR, 'conf')
TMP_KUBERNETES_MASTER_SSL_DIR = os.path.join(TMP_KUBERNETES_MASTER_DIR, 'ssl')
# ##node节点临时安装目录
TMP_KUBERNETES_NODE_DIR = os.path.join(TMP_KUBERNETES_HOME_DIR, 'node')
TMP_KUBERNETES_NODE_BIN_DIR = os.path.join(TMP_KUBERNETES_NODE_DIR, 'bin')
TMP_KUBERNETES_NODE_CONFIG_DIR = os.path.join(TMP_KUBERNETES_NODE_DIR, 'conf')
TMP_KUBERNETES_NODE_SSL_DIR = os.path.join(TMP_KUBERNETES_NODE_DIR, 'ssl')

# kubernetes
KUBERNETES_HOME = os.path.join(INSTALL_ROOT, "kubernetes")
KUBERNETES_CONFIG_DIR = os.path.join(KUBERNETES_HOME, "conf")
KUBERNETES_SSL_DIR = os.path.join(KUBERNETES_HOME, "ssl")
KUBERNETES_BIN_DIR = os.path.join(KUBERNETES_HOME, "bin")


if len(KUBERNETES_MASTER.values()) > 1:
    LEADER_ELECT = "true"
else:
    LEADER_ELECT = 'false'


# 配置相关信息
KUBE_CONTROLLER_MANAGER = {
    "KUBE_HOME": KUBERNETES_HOME,
    "CLUSTER_NAME": "kubernetes",
    "KUBE_USER": "system:kube-controller-manager",
    "KUBE_CERT": "sa",
    "KUBE_CONFIG": "controller-manager.kubeconfig"
}
# 设置集群参数
KUBE_SCHEDULER = {
    "KUBE_HOME": KUBERNETES_HOME,
    "CLUSTER_NAME": "kubernetes",
    "KUBE_USER": "system:kube-scheduler",
    "KUBE_CERT": "kube-scheduler",
    "KUBE_CONFIG": "scheduler.kubeconfig",
}
#
KUBE_ADMIN = {
    "KUBE_HOME": KUBERNETES_HOME,
    "CLUSTER_NAME": "kubernetes",
    "KUBE_USER": "kubernetes-admin",
    "KUBE_CERT": "admin",
    "KUBE_CONFIG": "admin.kubeconfig"
}
# BOOTSTRAP_TOKEN
TOKEN_PUB = ''.join(random.sample(string.ascii_letters + string.digits, 6)).lower()
TOKEN_SECRET = ''.join(random.sample(string.ascii_letters + string.digits, 16)).lower()

BOOTSTRAP_TOKEN = {
    "TOKEN_PUB": TOKEN_PUB,
    "TOKEN_SECRET": TOKEN_SECRET,
    "TOKEN": "{0}.{1}".format(TOKEN_PUB, TOKEN_SECRET),
    "CLUSTER_NAME": "kubernetes",
    "KUBE_USER": "kubelet-bootstrap",
    "KUBE_CONFIG": "bootstrap.kubeconfig"
}
KUBE_PROXY = {
    "CLUSTER_NAME": "kubernetes",
    "KUBE_CONFIG": "kube-proxy.kubeconfig"
}
KUBE_CONTROLLER_MANAGER_START_DICT = {
    "allocate-node-cidrs": 'true',
    "kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'controller-manager.kubeconfig'),
    "authentication-kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'controller-manager.kubeconfig'),
    "authorization-kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'controller-manager.kubeconfig'),
    "client-ca-file": os.path.join(KUBERNETES_SSL_DIR, "ca.crt"),
    "cluster-signing-cert-file": os.path.join(KUBERNETES_SSL_DIR, "ca.crt"),
    "cluster-signing-key-file": os.path.join(KUBERNETES_SSL_DIR, "ca.key"),
    "bind-address": "127.0.0.1",
    "leader-elect": LEADER_ELECT,
    "cluster-cidr": CLUSTER_ADDRESS,
    "service-cluster-ip-range": SERVICE_CLUSTER_IP_RANGE,
    "requestheader-client-ca-file": os.path.join(KUBERNETES_SSL_DIR, "front-proxy-ca.crt"),
    "service-account-private-key-file": os.path.join(KUBERNETES_SSL_DIR, "sa.key"),
    "root-ca-file": os.path.join(KUBERNETES_SSL_DIR, "ca.crt"),
    "use-service-account-credentials": "true",
    "controllers": "*,bootstrapsigner,tokencleaner",
    "experimental-cluster-signing-duration": "86700h",
    "feature-gates=RotateKubeletClientCertificate": "true",
    "v": 2
}

KUBE_APISERVER_START_DICT = {
    "authorization-mode": "Node,RBAC",
    "enable-admission-plugins": "NamespaceLifecycle,LimitRanger,ServiceAccount,PersistentVolumeClaimResize,"
                                "DefaultStorageClass,DefaultTolerationSeconds,NodeRestriction,"
                                "MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota,Priority,PodPreset",
    "advertise-address": "{0}",
    "bind-address": "{0}",
    "insecure-port": 0,
    "secure-port": KUBE_APISERVER_SECURE_PORT,
    "allow-privileged": "true",
    "apiserver-count": len(KUBERNETES_MASTER.values()),
    "audit-log-maxage": 30,
    "audit-log-maxbackup": 3,
    "audit-log-maxsize": 100,
    "audit-log-path": "/var/log/audit.log",
    "enable-swagger-ui": "true",
    "storage-backend": "etcd3",
    "etcd-cafile": os.path.join(KUBERNETES_SSL_DIR, 'etcd', 'ca.crt'),
    "etcd-certfile": os.path.join(KUBERNETES_SSL_DIR, 'apiserver-etcd-client.crt'),
    "etcd-keyfile": os.path.join(KUBERNETES_SSL_DIR, 'apiserver-etcd-client.key'),
    "etcd-servers": "https://{0}:2379".format(":2379,https://".join(ETCD_CLUSTER_LIST)),
    "event-ttl": "1h",
    "client-ca-file": os.path.join(KUBERNETES_SSL_DIR, 'ca.crt'),
    "tls-private-key-file": os.path.join(KUBERNETES_SSL_DIR, 'apiserver.key'),
    "kubelet-client-certificate": os.path.join(KUBERNETES_SSL_DIR, 'apiserver-kubelet-client.crt'),
    "kubelet-client-key": os.path.join(KUBERNETES_SSL_DIR, 'apiserver-kubelet-client.key'),
    "kubelet-preferred-address-types": "InternalIP,ExternalIP,Hostname",
    "runtime-config=api/all,settings.k8s.io/v1alpha1": "true",
    "service-cluster-ip-range": SERVICE_CLUSTER_IP_RANGE,
    "service-node-port-range": SERVICE_NODE_PORT_RANGE,
    "service-account-key-file": os.path.join(KUBERNETES_SSL_DIR, 'sa.pub'),
    "tls-cert-file": os.path.join(KUBERNETES_SSL_DIR, 'apiserver.crt'),
    "requestheader-client-ca-file": os.path.join(KUBERNETES_SSL_DIR, 'front-proxy-ca.crt'),
    "requestheader-username-headers": "X-Remote-User",
    "requestheader-group-headers": "X-Remote-Group",
    "requestheader-allowed-names": "front-proxy-client",
    "requestheader-extra-headers-prefix": "X-Remote-Extra-",
    "proxy-client-cert-file": os.path.join(KUBERNETES_SSL_DIR, 'front-proxy-client.crt'),
    "proxy-client-key-file": os.path.join(KUBERNETES_SSL_DIR, 'front-proxy-client.key'),
    "feature-gates": "PodShareProcessNamespace=true",
    "runtime-config=api/all": "true",
    "v": 2
}
KUBE_SCHEDULER_START_DICT = {
    "leader-elect": LEADER_ELECT,
    "kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'scheduler.kubeconfig'),
    "authorization-kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'scheduler.kubeconfig'),
    "authentication-kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'scheduler.kubeconfig'),
    "address": "127.0.0.1",
    "v": 2
}
# ###############################Node###############################################
KUBE_KUBELET_START_DICT = {
    "bootstrap-kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'bootstrap.kubeconfig'),
    "kubeconfig": os.path.join(KUBERNETES_CONFIG_DIR, 'kubelet.kubeconfig'),
    "config": os.path.join(KUBERNETES_CONFIG_DIR, 'kubelet-conf.yaml'),
    "pod-infra-container-image": IMAGE_DICT['pause'],
    "network-plugin": "cni",
    "cni-conf-dir": CNI_CONFIG_DIR,
    "cni-bin-dir": CNI_BIN_DIR,
    "cert-dir": KUBERNETES_SSL_DIR,
    "cgroup-driver": "cgroupfs",
    "v": 2
}
KUBELET_CONFIG_DICT = {
    'enforceNodeAllocatable': ['pods'],
    'eventRecordQPS': 5,
    'kubeAPIQPS': 5,
    'makeIPTablesUtilChains': True,
    'httpCheckFrequency': '20s',
    'cgroupsPerQOS': True,
    'serializeImagePulls': True,
    'runtimeRequestTimeout': '2m0s',
    'nodeStatusUpdateFrequency': '10s',
    'enableDebuggingHandlers': True,
    'registryBurst': 10,
    'port': 10250,
    'healthzBindAddress': '127.0.0.1',
    'streamingConnectionIdleTimeout': '4h0m0s',
    'maxOpenFiles': 1000000,
    'podPidsLimit': -1,
    'volumeStatsAggPeriod': '1m0s',
    'authentication': {
        'x509': {
            'clientCAFile': os.path.join(KUBERNETES_SSL_DIR, 'ca.crt')
        },
        'webhook': {'enabled': True, 'cacheTTL': '2m0s'},
        'anonymous': {'enabled': False}
    },
    'evictionPressureTransitionPeriod': '5m0s',
    'cgroupDriver': 'systemd',
    'apiVersion': 'kubelet.config.k8s.io/v1beta1',
    'nodeLeaseDurationSeconds': 40,
    'fileCheckFrequency': '20s',
    'imageGCLowThresholdPercent': 80,
    'registryPullQPS': 5,
    'authorization': {
        'webhook': {
            'cacheUnauthorizedTTL': '30s',
            'cacheAuthorizedTTL': '5m0s'
        },
        'mode': 'Webhook'
    },
    'eventBurst': 10,
    'failSwapOn': True,
    'kubeAPIBurst': 10,
    'iptablesMasqueradeBit': 14,
    'hairpinMode': 'promiscuous-bridge',
    'cpuManagerPolicy': 'none',
    'cpuCFSQuota': True,
    'evictionHard': {
        'imagefs.available': '15%',
        'memory.available': '100Mi',
        'nodefs.inodesFree': '5%',
        'nodefs.available': '10%'
    },
    'clusterDNS': DNS_IP,
    'clusterDomain': 'cluster.local',
    'imageMinimumGCAge': '2m0s',
    'resolvConf': '/etc/resolv.conf',
    'oomScoreAdj': -999,
    'address': '0.0.0.0',
    'syncFrequency': '1m0s',
    'healthzPort': 10248,
    'nodeStatusReportFrequency': '1m0s',
    'contentType': 'application/vnd.kubernetes.protobuf',
    'kind': 'KubeletConfiguration',
    'containerLogMaxFiles': 5,
    'staticPodPath': os.path.join(KUBERNETES_CONFIG_DIR, 'manifests'),
    'imageGCHighThresholdPercent': 85,
    'enableControllerAttachDetach': True,
    'containerLogMaxSize': '10Mi',
    'iptablesDropBit': 15, 'maxPods': 110,
    'cpuManagerReconcilePeriod': '10s',
    'configMapAndSecretChangeDetectionStrategy': 'Watch',
    'cpuCFSQuotaPeriod': '100ms',
    'rotateCertificates': True
}

KUBEPROXY_CONFIG_DICT = {
    'iptables': {
        'masqueradeAll': True,
        'syncPeriod': '30s',
        'masqueradeBit': 14,
        'minSyncPeriod': '0s'
    },
    'nodePortAddresses': None,
    'hostnameOverride': '',
    'conntrack': {
        'maxPerCore': 32768,
        'max': None,
        'tcpCloseWaitTimeout': '1h0m0s',
        'tcpEstablishedTimeout': '24h0m0s',
        'min': 131072
    },
    'resourceContainer': '/kube-proxy',
    'bindAddress': '0.0.0.0',
    'metricsBindAddress': '127.0.0.1:10249',
    'udpIdleTimeout': '250ms',
    'configSyncPeriod': '15m0s',
    'oomScoreAdj': -999,
    'enableProfiling': False,
    'clusterCIDR': CLUSTER_ADDRESS,
    'kind': 'KubeProxyConfiguration',
    'portRange': '',
    'apiVersion': 'kubeproxy.config.k8s.io/v1alpha1',
    'healthzBindAddress': '0.0.0.0:10256',
    'clientConnection': {
        'qps': 5,
        'burst': 10,
        'contentType': 'application/vnd.kubernetes.protobuf',
        'acceptContentTypes': '',
        'kubeconfig': os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.kubeconfig')
    }
}

__all__ = [
    'KUBERNETES_SSL_DIR',
    'KUBERNETES_BIN_DIR',
    'KUBERNETES_CONFIG_DIR',
    'KUBERNETES_HOME',
    'KUBE_ADMIN',
    'KUBE_CONTROLLER_MANAGER',
    'KUBE_SCHEDULER',
    'KUBE_PROXY',
    'BOOTSTRAP_TOKEN',
    'TOKEN_SECRET',
    'TOKEN_PUB',
    'KUBEPROXY_CONFIG_DICT',
    'KUBELET_CONFIG_DICT',
    'KUBERNETES_MASTER_PACKAGE',
    'KUBERNETES_NODE_PACKAGE',
    'TMP_KUBERNETES_MASTER_DIR',
    'TMP_KUBERNETES_MASTER_SSL_DIR',
    'TMP_KUBERNETES_MASTER_BIN_DIR',
    'TMP_KUBERNETES_MASTER_CONFIG_DIR',
    'TMP_KUBERNETES_NODE_BIN_DIR',
    'TMP_KUBERNETES_NODE_CONFIG_DIR',
    'TMP_KUBERNETES_NODE_SSL_DIR',
    'TMP_KUBERNETES_NODE_DIR',
    'KUBE_APISERVER_START_DICT',
    'KUBE_CONTROLLER_MANAGER_START_DICT',
    'KUBE_KUBELET_START_DICT',
    'KUBE_SCHEDULER_START_DICT',
    'TMP_PACKAGE_PATH',
    'TMP_ROOT_DIR'
]
