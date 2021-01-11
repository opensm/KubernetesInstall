import os
from lib.settings import ETCD_CLUSTER_LIST
from lib.setting.cni import CNI_CONFIG_DIR, CNI_BIN_DIR

initial_cluster = ""
for x in range(0, len(ETCD_CLUSTER_LIST)):
    initial_cluster = "%s,etcd%02d=https://%s:2380" % (initial_cluster, (x + 1), ETCD_CLUSTER_LIST[x])

CALICO_NODE = {
    'kind': 'DaemonSet',
    'spec': {
        'updateStrategy': {
            'rollingUpdate': {
                'maxUnavailable': 1
            },
            'type': 'RollingUpdate'
        },
        'template': {
            'spec': {
                'priorityClassName': 'system-node-critical',
                'serviceAccountName': 'calico-node',
                'hostNetwork': True,
                'nodeSelector': {
                    'beta.kubernetes.io/os': 'linux'
                },
                'terminationGracePeriodSeconds': 0,
                'volumes': [
                    {
                        'hostPath': {
                            'path': '/lib/modules'
                        },
                        'name': 'lib-modules'
                    },
                    {
                        'hostPath': {
                            'path': '/var/run/calico'
                        },
                        'name': 'var-run-calico'
                    },
                    {
                        'hostPath': {
                            'path': '/var/lib/calico'
                        },
                        'name': 'var-lib-calico'
                    },
                    {
                        'hostPath': {
                            'path': '/run/xtables.lock', 'type': 'FileOrCreate'
                        },
                        'name': 'xtables-lock'
                    }, {
                        'hostPath': {
                            'path': CNI_BIN_DIR
                        }, 'name': 'cni-bin-dir'
                    }, {
                        'hostPath': {
                            'path': CNI_CONFIG_DIR
                        },
                        'name': 'cni-net-dir'
                    }, {
                        'hostPath': {
                            'path': '/var/lib/cni/networks'
                        }, 'name': 'host-local-net-dir'
                    }, {
                        'hostPath': {
                            'path': '/var/run/nodeagent',
                            'type': 'DirectoryOrCreate'
                        },
                        'name': 'policysync'
                    }, {
                        'hostPath': {
                            'path': '/usr/libexec/kubernetes/kubelet-plugins/volume/exec/nodeagent~uds',
                            'type': 'DirectoryOrCreate'
                        }, 'name': 'flexvol-driver-host'
                    }],
                'tolerations': [{
                    'operator': 'Exists',
                    'effect': 'NoSchedule'
                }, {
                    'operator': 'Exists', 'key': 'CriticalAddonsOnly'
                }, {
                    'operator': 'Exists', 'effect': 'NoExecute'
                }],
                'initContainers': [
                    {
                        'command': ['/opt/cni/bin/calico-ipam', '-upgrade'],
                        'image': 'calico/cni:v3.9.6',
                        'volumeMounts': [{
                            'mountPath': '/var/lib/cni/networks',
                            'name': 'host-local-net-dir'
                        }, {
                            'mountPath': '/host/opt/cni/bin',
                            'name': 'cni-bin-dir'
                        }],
                        'name': 'upgrade-ipam',
                        'env': [{
                            'valueFrom': {
                                'fieldRef': {
                                    'fieldPath': 'spec.nodeName'
                                }
                            },
                            'name': 'KUBERNETES_NODE_NAME'
                        }, {
                            'valueFrom': {
                                'configMapKeyRef': {
                                    'name': 'calico-config',
                                    'key': 'calico_backend'
                                }},
                            'name': 'CALICO_NETWORKING_BACKEND'
                        }]},
                    {
                        'command': ['/install-cni.sh'],
                        'image': 'calico/cni:v3.9.6',
                        'volumeMounts': [{
                            'mountPath': '/host/opt/cni/bin',
                            'name': 'cni-bin-dir'
                        }, {
                            'mountPath': '/host/etc/cni/net.d',
                            'name': 'cni-net-dir'
                        }],
                        'name': 'install-cni',
                        'env': [{
                            'name': 'CNI_CONF_NAME',
                            'value': '10-calico.conflist'
                        }, {
                            'valueFrom': {
                                'configMapKeyRef': {
                                    'name': 'calico-config',
                                    'key': 'cni_network_config'
                                }
                            },
                            'name': 'CNI_NETWORK_CONFIG'
                        }, {
                            'valueFrom': {
                                'fieldRef': {
                                    'fieldPath': 'spec.nodeName'
                                }
                            },
                            'name': 'KUBERNETES_NODE_NAME'
                        }, {
                            'valueFrom': {
                                'configMapKeyRef': {
                                    'name': 'calico-config',
                                    'key': 'veth_mtu'
                                }
                            },
                            'name': 'CNI_MTU'
                        }, {
                            'name': 'SLEEP',
                            'value': 'false'
                        }]
                    }, {
                        'image': 'calico/pod2daemon-flexvol:v3.9.6',
                        'volumeMounts': [{
                            'mountPath': '/host/driver',
                            'name': 'flexvol-driver-host'
                        }],
                        'name': 'flexvol-driver'
                    }],
                'containers': [{
                    'livenessProbe': {
                        'initialDelaySeconds': 10,
                        'failureThreshold': 6,
                        'exec': {
                            'command': ['/bin/calico-node', '-felix-live', '-bird-live']
                        },
                        'periodSeconds': 10
                    }, 'securityContext': {
                        'privileged': True
                    },
                    'name': 'calico-node',
                    'image': 'calico/node:v3.9.6',
                    'volumeMounts': [{
                        'readOnly': True,
                        'mountPath': '/lib/modules',
                        'name': 'lib-modules'
                    }, {
                        'readOnly': False,
                        'mountPath': '/run/xtables.lock',
                        'name': 'xtables-lock'
                    }, {
                        'readOnly': False,
                        'mountPath': '/var/run/calico',
                        'name': 'var-run-calico'
                    }, {
                        'readOnly': False,
                        'mountPath': '/var/lib/calico',
                        'name': 'var-lib-calico'
                    }, {
                        'mountPath': '/var/run/nodeagent',
                        'name': 'policysync'
                    }],
                    'env': [{
                        'name': 'DATASTORE_TYPE',
                        'value': 'kubernetes'
                    }, {
                        'name': 'WAIT_FOR_DATASTORE',
                        'value': 'true'
                    }, {
                        'valueFrom': {
                            'fieldRef': {
                                'fieldPath': 'spec.nodeName'
                            }},
                        'name': 'NODENAME'
                    }, {
                        'valueFrom': {
                            'configMapKeyRef': {
                                'name': 'calico-config',
                                'key': 'calico_backend'
                            }},
                        'name': 'CALICO_NETWORKING_BACKEND'
                    }, {
                        'name': 'CLUSTER_TYPE',
                        'value': 'k8s,bgp'
                    }, {
                        'name': 'IP',
                        'value': 'autodetect'
                    }, {
                        'name': 'CALICO_IPV4POOL_IPIP',
                        'value': 'Always'
                    }, {
                        'valueFrom': {
                            'configMapKeyRef': {
                                'name': 'calico-config',
                                'key': 'veth_mtu'
                            }},
                        'name': 'FELIX_IPINIPMTU'
                    }, {
                        'name': 'CALICO_IPV4POOL_CIDR',
                        'value': '10.244.0.0/16'
                    }, {
                        'name': 'CALICO_DISABLE_FILE_LOGGING',
                        'value': 'true'
                    }, {
                        'name': 'FELIX_DEFAULTENDPOINTTOHOSTACTION',
                        'value': 'ACCEPT'
                    }, {
                        'name': 'FELIX_IPV6SUPPORT',
                        'value': 'false'
                    }, {
                        'name': 'FELIX_LOGSEVERITYSCREEN',
                        'value': 'info'
                    }, {
                        'name': 'FELIX_HEALTHENABLED',
                        'value': 'true'
                    }],
                    'readinessProbe': {
                        'exec': {
                            'command': [
                                '/bin/calico-node',
                                '-felix-ready',
                                '-bird-ready'
                            ]},
                        'periodSeconds': 10
                    },
                    'resources': {
                        'requests': {
                            'cpu': '250m'
                        }
                    }
                }]
            },
            'metadata': {
                'labels': {
                    'k8s-app': 'calico-node'
                }, 'annotations': {
                    'scheduler.alpha.kubernetes.io/critical-pod': ''
                }
            }
        },
        'selector': {
            'matchLabels': {
                'k8s-app': 'calico-node'
            }
        }
    },
    'apiVersion': 'apps/v1',
    'metadata': {
        'labels': {
            'k8s-app': 'calico-node'
        },
        'namespace': 'kube-system',
        'name': 'calico-node'
    }
}
CALICO_CONFIG = {
    'kind': 'ConfigMap',
    'data': {
        'calico_backend': 'bird',
        'veth_mtu': '1440',
        'cni_network_config': '{\n  "name": "k8s-pod-network",\n  "cniVersion": "0.3.1",\n  "plugins": [\n    {\n      "type": "calico",\n      "log_level": "info",\n      "datastore_type": "kubernetes",\n      "nodename": "__KUBERNETES_NODE_NAME__",\n      "mtu": __CNI_MTU__,\n      "ipam": {\n          "type": "calico-ipam"\n      },\n      "policy": {\n          "type": "k8s"\n      },\n      "kubernetes": {\n          "kubeconfig": "%s"\n      }\n    },\n    {\n      "type": "portmap",\n      "snat": true,\n      "capabilities": {"portMappings": true}\n    }\n  ]\n}' %
                              os.path.join(CNI_CONFIG_DIR, 'calico-kubeconfig'),
        'typha_service_name': 'none'
    },
    'apiVersion': 'v1',
    'metadata': {
        'namespace': 'kube-system',
        'name': 'calico-config'
    }
}

__all__ = ['CNI_CONFIG_DIR', 'CNI_BIN_DIR', 'CALICO_CONFIG', 'CALICO_NODE']
