# -*- coding: utf-8 -*-
import copy
import shutil
import os
import time
from lib.PyKubernetes import PyKubernetes
from lib.BaseCommand import LocalExec, SSHFtp
from lib.Log import RecodeLog
from lib.OpenSSlControl import Cf
from lib.FileCommand import Achieve
from lib.setting.kube import *
from lib.setting.cni import CNI_CONFIG_DIR
from lib.setting.base import *
from lib.setting.openssl import OPENSSL_TMP_DIR
from lib.settings import KUBERNETES_MASTER, KUBERNETES_NODE, KUBERNETES_APISERVER, AUTHENTICATION
from lib.dependent import get_cluster_list


class KubernetesInstall:
    def __init__(self):
        created_dirs = [
            TMP_ROOT_DIR,
            TMP_SYSTEMCTL_DIR,
            TMP_KUBERNETES_MASTER_SSL_DIR,
            TMP_KUBERNETES_MASTER_BIN_DIR,
            os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'manifests'),
            os.path.join(TMP_KUBERNETES_NODE_CONFIG_DIR, 'manifests'),
            TMP_KUBERNETES_NODE_SSL_DIR,
            TMP_KUBERNETES_NODE_BIN_DIR
        ]
        checked_dirs = [
            KUBERNETES_MASTER_PACKAGE,
            KUBERNETES_NODE_PACKAGE
        ]
        Achieve.check_dirs(dir_list=created_dirs, create=True)
        Achieve.check_dirs(dir_list=checked_dirs, create=False)
        self.kubectl_bin = os.path.join(TMP_KUBERNETES_MASTER_BIN_DIR, 'kubectl')
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)
        self.pykube = PyKubernetes()

    def server_decompression(self):
        """
        :return:
        """
        # 判断当前安装目录是否存在主目录，存在就将其移走
        if os.path.exists(TMP_KUBERNETES_MASTER_DIR):
            shutil.move(
                src=TMP_KUBERNETES_MASTER_DIR,
                dst="{0}.{1}".format(TMP_KUBERNETES_MASTER_DIR, int(time.time()))
            )
        # 解压文件
        if not Achieve.tar_decompression(
                achieve=KUBERNETES_MASTER_PACKAGE,
                target_path=TMP_ROOT_DIR
        ):
            RecodeLog.error(msg="解压文件失败：{0}!".format(KUBERNETES_MASTER_PACKAGE))
            assert False
        try:
            shutil.copytree(
                OPENSSL_TMP_DIR,
                TMP_KUBERNETES_MASTER_SSL_DIR
            )
            RecodeLog.info(
                msg="kubernetes server拷贝证书到临时目录成功：{0}!".format(
                    TMP_KUBERNETES_MASTER_SSL_DIR
                )
            )
        except Exception as error:
            RecodeLog.error(
                msg="kubernetes server拷贝证书到临时目录失败：{0},{1}!".format(
                    TMP_KUBERNETES_MASTER_SSL_DIR, error
                )
            )
            assert False
        # 生成变量
        control_manager = copy.deepcopy(KUBE_CONTROLLER_MANAGER)
        scheduler = copy.deepcopy(KUBE_SCHEDULER)
        admin = copy.deepcopy(KUBE_ADMIN)
        # 生成临时配置
        # 生成集群的配置文件 controller-manager.kubeconfig
        assert self.kubernetes_tmp_conf(params=control_manager)
        # 生成集群的配置文件 scheduler.kubeconfig
        assert self.kubernetes_tmp_conf(params=scheduler)
        # 生成集群的配置文件 admin.kubeconfig
        assert self.kubernetes_tmp_conf(params=admin)

        # 相应的启动脚本生成
        self.manager_service()
        self.scheduler_service()
        for value in KUBERNETES_MASTER.values():
            self.apiserver_service(host=value)

    @staticmethod
    def make_start_string(start_string, start_dict):
        if not isinstance(start_string, str):
            raise TypeError('{0} 类型不为str!'.format(start_string))
        if not isinstance(start_dict, dict):
            raise TypeError('{0} 类型不为dict!'.format(start_dict))
        if len(start_dict) == 0:
            raise ValueError("start_dict 为空！ ")
        start = start_string
        for key, value in start_dict.items():
            start = "{0} --{1}={2}".format(start, key, value)
        return start

    @staticmethod
    def node_decompression():
        """
        :return:
        """
        # 解压文件
        if not Achieve.tar_decompression(
                achieve=KUBERNETES_NODE_PACKAGE,
                target_path=TMP_ROOT_DIR
        ):
            RecodeLog.error(msg="解压文件失败：{0}!".format(KUBERNETES_NODE_PACKAGE))
            assert False
        ca_file = os.path.join(OPENSSL_TMP_DIR, 'ca.crt')
        shutil.copy(ca_file, TMP_KUBERNETES_NODE_SSL_DIR)

    @staticmethod
    def kubernetes_tmp_conf(params):
        """
        :param params:
        :return:
        """
        if not isinstance(params, dict):
            return False
        if not os.path.exists(TMP_KUBERNETES_MASTER_CONFIG_DIR):
            os.makedirs(TMP_KUBERNETES_MASTER_CONFIG_DIR)
            RecodeLog.info(msg="创建:{0},成功！".format(TMP_KUBERNETES_MASTER_CONFIG_DIR))
        control_params = [
            TMP_KUBERNETES_MASTER_BIN_DIR,
            TMP_KUBERNETES_MASTER_CONFIG_DIR,
            TMP_KUBERNETES_MASTER_SSL_DIR,
            params['CLUSTER_NAME'],
            params['KUBE_USER'],
            params['KUBE_CERT'],
            params['KUBE_CONFIG'],
            KUBERNETES_APISERVER
        ]
        config_achieve = os.path.join(CMD_FILE_DIR, params['KUBE_CONFIG'])

        if not LocalExec.cmd_with_files(
                achieve_object=Achieve,
                achieve=config_achieve,
                params=control_params
        ):
            RecodeLog.error(msg="执行失败！")
            return False
        else:
            return True

    def manager_service(self):
        """
        :return:
        """
        start_string = os.path.join(KUBERNETES_BIN_DIR, 'kube-controller-manager')
        exec_start = self.make_start_string(
            start_string=start_string,
            start_dict=KUBE_CONTROLLER_MANAGER_START_DICT
        )
        data = {
            'ExecStart': exec_start,
            "Restart": "always",
            "RestartSec": "10s",
            "Type": "simple",
        }
        source_achieve = os.path.join(TMP_SYSTEMCTL_DIR, 'kube-controller-manager.service')
        dst_achieve = os.path.join(TMP_KUBERNETES_MASTER_DIR, 'kube-controller-manager.service')
        try:
            shutil.copy(src=source_achieve, dst=dst_achieve)
        except Exception as error:
            RecodeLog.error(
                msg="拷贝文件:{0},失败，原因:{1}".format(
                    source_achieve,
                    error
                )
            )
            assert False
        if not Cf.write_achieve(
                achieve=dst_achieve,
                sections="Service",
                data=data,
                upper=False
        ):
            assert False

    def apiserver_service(self, host):
        """
        :param host:
        :return:
        """
        start_string = "{0} --kubelet-https --enable-bootstrap-token-auth".format(
            os.path.join(
                KUBERNETES_BIN_DIR, 'kube-apiserver'
            ))
        exec_start = self.make_start_string(
            start_string=start_string,
            start_dict=KUBE_APISERVER_START_DICT
        ).format(host)
        RecodeLog.debug(msg=exec_start)
        source_achieve = os.path.join(
            TMP_SYSTEMCTL_DIR,
            'kube-apiserver.service'
        )
        dst_achieve = os.path.join(TMP_KUBERNETES_MASTER_DIR, '{0}_kube-apiserver.service'.format(host))
        data = {
            'ExecStart': exec_start,
            "Restart": "on-failure",
            "RestartSec": "10s",
            "Type": "simple",
            "LimitNOFILE": 65535
        }
        try:
            shutil.copy(src=source_achieve, dst=dst_achieve)
        except Exception as error:
            RecodeLog.error(msg="拷贝文件:{0},失败，原因:{1}".format(
                source_achieve,
                error
            ))
            return False
        if not Cf.write_achieve(achieve=dst_achieve, sections="Service", data=data, upper=False):
            return False
        else:
            return True

    def scheduler_service(self):
        """
        :return:
        """
        start_string = os.path.join(KUBERNETES_BIN_DIR, 'kube-scheduler')
        exec_start = self.make_start_string(
            start_string=start_string,
            start_dict=KUBE_SCHEDULER_START_DICT
        )
        dst_achieve = os.path.join(TMP_KUBERNETES_MASTER_DIR, 'kube-scheduler.service')
        source_achieve = os.path.join(TMP_SYSTEMCTL_DIR, 'kube-scheduler.service')
        data = {
            'ExecStart': exec_start,
            "Restart": "always",
            "Type": "simple",
            "RestartSec": "10s"
        }

        try:
            shutil.copy(src=source_achieve, dst=dst_achieve)
        except Exception as error:
            RecodeLog.error(msg="拷贝文件:{0},失败，原因:{1}".format(
                source_achieve,
                error
            ))
            return False
        if not Cf.write_achieve(
                achieve=dst_achieve,
                sections="Service",
                data=data,
                upper=False
        ):
            return False
        else:
            return True

    @staticmethod
    def generic_bootstrap_token(params):
        """
        :return:
        """

        if not isinstance(params, dict):
            return False
        control_params = [
            TMP_KUBERNETES_MASTER_BIN_DIR,
            TMP_KUBERNETES_MASTER_CONFIG_DIR,
            TMP_KUBERNETES_MASTER_SSL_DIR,
            params['CLUSTER_NAME'],
            params['KUBE_USER'],
            params['KUBE_CONFIG'],
            params['TOKEN'],
            KUBERNETES_APISERVER,
            params['TOKEN_PUB'],
            params['TOKEN_SECRET']
        ]
        config_achieve = os.path.join(
            CMD_FILE_DIR, params['KUBE_CONFIG']
        )

        if not LocalExec.cmd_with_files(
                achieve_object=Achieve,
                achieve=config_achieve,
                params=control_params
        ):
            RecodeLog.error(msg="生成BOOTSTRAP_TOKEN失败!")
            return False
        else:
            RecodeLog.info(msg="生成BOOTSTRAP_TOKEN成功！")
            return True

    def server_rsync_install(self):
        """
        :return:
        """
        config_file = os.path.join(KUBERNETES_CONFIG_DIR, 'kubelet-conf.yaml')
        for key, value in KUBERNETES_MASTER.items():
            self.sftp.host = value
            self.sftp.connect()
            # 拷贝完整的server端到服务点
            self.sftp.sftp_put_dir(
                local_dir=TMP_KUBERNETES_MASTER_DIR,
                remote_dir=KUBERNETES_HOME
            )
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, KUBE_ADMIN['KUBE_CONFIG']),
                remotefile="/root/.kube/config"
            )
            local_config = os.path.join(
                TMP_KUBERNETES_MASTER_CONFIG_DIR,
                '{0}_kubelet-conf.yaml'.format(value)
            )
            self.sftp.sftp_put(localfile=local_config, remotefile=config_file)
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_DIR, 'kubelet.service'),
                remotefile=os.path.join(KUBERNETES_HOME, 'kubelet.service')
            )
            self.sftp.remote_cmd(command="chmod 700 {0} && ln -sf {0} /usr/local/bin/".format(
                os.path.join(KUBERNETES_BIN_DIR, '*')
            ))
            self.sftp.remote_cmd(command="[[ ! -f {1} ]] || rm -f {1} && cp -f {0} {1}".format(
                os.path.join(
                    KUBERNETES_HOME, '{0}_kube-apiserver.service'.format(value),
                ),
                os.path.join(SYSTEMCTL_DIR, 'kube-apiserver.service')
            ))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kube-controller-manager.service'),
                SYSTEMCTL_DIR
            ))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kubelet.service'),
                SYSTEMCTL_DIR
            ))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kube-scheduler.service'),
                SYSTEMCTL_DIR
            ))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kube-proxy.service'),
                SYSTEMCTL_DIR
            ))

            self.sftp.close()

    def bootstrappers_install(self):
        """
        :return:
        """
        RecodeLog.info("=============开始生成同步到其他节点kube-bootstrappers===============")
        check_file = os.path.join(TAG_FILE_DIR, 'kubernetes_bootstrappers.success')
        if os.path.exists(check_file):
            return True
        bootstrap = copy.deepcopy(BOOTSTRAP_TOKEN)
        self.generic_bootstrap_token(params=bootstrap)
        if not os.path.exists(
                os.path.join(
                    TMP_KUBERNETES_MASTER_CONFIG_DIR,
                    'bootstrap.kubeconfig'
                )
        ):
            assert False
        bootstrap_cmd = """{0} create clusterrolebinding kubeadm:kubelet-bootstrap \
        --clusterrole system:node-bootstrapper --group system:bootstrappers""".format(
            self.kubectl_bin
        )
        self.kube_apply()
        LocalExec.cmd(cmd_command=bootstrap_cmd, result=False)
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'bootstrap.kubeconfig'),
                remotefile=os.path.join(KUBERNETES_CONFIG_DIR, 'bootstrap.kubeconfig')
            )
            self.sftp.close()

        for value in KUBERNETES_NODE.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.sftp_put(
                localfile=os.path.join(
                    TMP_KUBERNETES_MASTER_CONFIG_DIR,
                    'bootstrap.kubeconfig'
                ),
                remotefile=os.path.join(
                    KUBERNETES_CONFIG_DIR,
                    'bootstrap.kubeconfig'
                )
            )
            self.sftp.close()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============开始同步到其他节点kube-bootstrappers===============")

    def kubelet_service(self):
        """
        :return:
        """
        exec_start = self.make_start_string(
            start_string=os.path.join(KUBERNETES_BIN_DIR, 'kubelet'),
            start_dict=KUBE_KUBELET_START_DICT
        )
        source_achieve = os.path.join(TMP_SYSTEMCTL_DIR, 'kubelet.service')
        for path in [TMP_KUBERNETES_MASTER_DIR, TMP_KUBERNETES_NODE_DIR]:
            dst_achieve = os.path.join(path, 'kubelet.service')
            data = {
                'ExecStart': exec_start,
                "Restart": "always",
                "RestartSec": "10s"
            }
            try:
                shutil.copy(src=source_achieve, dst=dst_achieve)
            except Exception as error:
                RecodeLog.error(msg="拷贝文件:{0},失败，原因:{1}".format(
                    source_achieve,
                    error
                ))
                return False
            if not Cf.write_achieve(
                    achieve=dst_achieve,
                    sections="Service",
                    data=data,
                    upper=False
            ):
                return False

    @staticmethod
    def kubelet_config():
        """
        :return: 生成kubectl-conf.yaml文件
        """
        for value in KUBERNETES_MASTER.values():
            dst_service = os.path.join(
                TMP_KUBERNETES_MASTER_CONFIG_DIR,
                '{0}_kubelet-conf.yaml'.format(value)
            )
            KUBELET_CONFIG_DICT['healthzBindAddress'] = value
            KUBELET_CONFIG_DICT['address'] = value
            if not Achieve.write_yaml(
                    yaml_name=dst_service,
                    content=KUBELET_CONFIG_DICT
            ):
                assert False

        for value in KUBERNETES_NODE.values():
            dst_service = os.path.join(TMP_KUBERNETES_NODE_CONFIG_DIR, '{0}_kubelet-conf.yaml'.format(value))
            KUBELET_CONFIG_DICT['healthzBindAddress'] = value
            KUBELET_CONFIG_DICT['address'] = value
            if not Achieve.write_yaml(
                    yaml_name=dst_service,
                    content=KUBELET_CONFIG_DICT
            ):
                assert False

    def node_rsync_install(self):
        """
        :return: 远程安装 k8s node
        """
        config_file = os.path.join(KUBERNETES_CONFIG_DIR, 'kubelet-conf.yaml')
        for value in KUBERNETES_NODE.values():
            # 跳过master与node重复的部分
            if value in KUBERNETES_MASTER.values():
                continue
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.sftp_put_dir(
                local_dir=TMP_KUBERNETES_NODE_DIR,
                remote_dir=KUBERNETES_HOME
            )
            local_config = os.path.join(TMP_KUBERNETES_NODE_CONFIG_DIR, '{0}_kubelet-conf.yaml'.format(value))
            self.sftp.sftp_put(
                localfile=local_config,
                remotefile=config_file
            )
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_NODE_DIR, 'kubelet.service'),
                remotefile=os.path.join(KUBERNETES_HOME, 'kubelet.service')
            )
            self.sftp.remote_cmd(command="chmod 700 {0} && ln -sf {0} /usr/local/bin/".format(
                os.path.join(KUBERNETES_BIN_DIR, '*')))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kubelet.service'),
                SYSTEMCTL_DIR
            ))
            self.sftp.remote_cmd(command="ln -sf {0} {1}".format(
                os.path.join(KUBERNETES_HOME, 'kube-proxy.service'),
                SYSTEMCTL_DIR
            ))
            self.sftp.close()

    def enable_master_service(self):
        """
        :return: 执行启动/关闭k8s server
        """
        master_service = ['kube-apiserver', 'kube-scheduler', 'kube-controller-manager']
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command='/bin/systemctl daemon-reload')
            for service in master_service:
                self.sftp.remote_cmd(
                    command='/bin/systemctl disable {0} && /bin/systemctl enable {0}'.format(service)
                )
            self.sftp.close()

    def start_master_service(self):
        """
        :return: 执行启动/关闭k8s server
        """
        master_service = ['kube-apiserver', 'kube-scheduler', 'kube-controller-manager']
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            for service in master_service:
                self.sftp.remote_cmd(command='/bin/systemctl start  {0}'.format(service))
            self.sftp.close()

    def alias_kubelet(self):
        """
        :return:
        """
        exec_path = '/usr/local/bin'
        kubelet_bin = os.path.join(exec_path, 'kubelet')
        if not os.path.join(self.kubectl_bin):
            raise Exception("{0} not exist".format(self.kubectl_bin))
        if not os.path.exists(kubelet_bin):
            command = 'ln -sf {0} {1}'.format(self.kubectl_bin, kubelet_bin)
            LocalExec.cmd(cmd_command=command)

    @staticmethod
    def kube_apply():
        """
        :return:
        """
        command = "bash {0}".format(os.path.join(TMP_PACKAGE_PATH, 'auto-approve.sh'))
        LocalExec.cmd(cmd_command=command)

    def start_kubelet(self):
        """
        :return:
        """
        for value in get_cluster_list():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command="/bin/systemctl daemon-reload")
            self.sftp.remote_cmd(command="/bin/systemctl disable kubelet.service")
            self.sftp.remote_cmd(command="/bin/systemctl enable kubelet.service")
            self.sftp.remote_cmd(command="/bin/systemctl start kubelet.service")
            self.sftp.close()

    def tag_cluster(self):
        """
        :return: 给集群打标签
        """
        continue_run = ""
        while continue_run.upper() not in ['YES', 'Y']:
            continue_run = raw_input("集群的节点已启动，请根据列表确认是否继续,选择YES继续下一步，选择NO查看已加入集群的列表？yes/YES or NO/no:")
            if not isinstance(continue_run, str):
                RecodeLog.error(msg="输入类型错误")
                assert False
            if continue_run.upper() in ['YES', 'Y']:
                break
            else:
                command = "{0} get nodes".format(os.path.join(TMP_KUBERNETES_MASTER_BIN_DIR, 'kubectl'))
                RecodeLog.info(LocalExec.cmd(cmd_command=command))
                continue
        command = '''{0} label node {1} node-role.kubernetes.io/master=""'''.format(
            self.kubectl_bin, ' '.join(KUBERNETES_MASTER.keys())
        )
        LocalExec.cmd(cmd_command=command)

        command = '''{0} label node {1} node-role.kubernetes.io/node=""'''.format(
            self.kubectl_bin, ' '.join(KUBERNETES_NODE.keys())
        )
        LocalExec.cmd(cmd_command=command)
        create_service = """{0} -n kube-system create serviceaccount kube-proxy""".format(self.kubectl_bin)
        clusterrolebinding = """{0} create clusterrolebinding kubeadm:kube-proxy """ \
                             """--clusterrole system:node-proxier """ \
                             """--serviceaccount kube-system:kube-proxy""".format(self.kubectl_bin)

        LocalExec.cmd(cmd_command=create_service)
        LocalExec.cmd(cmd_command=clusterrolebinding)

    def kube_proxy_config(self, params):
        """
        :param
        :return:
        """
        secret_cmd = """%s -n kube-system get sa/kube-proxy """ \
                     """--output=jsonpath='{.secrets[0].name}'""" % (
                         self.kubectl_bin
                     )
        secret = LocalExec.cmd(cmd_command=secret_cmd, result=True)
        if not secret:
            RecodeLog.error(msg="生成kube-proxy secret失败!")
            assert False
        jwt_cmd = """%s -n kube-system get secret/%s """ \
                  """--output=jsonpath='{.data.token}' | base64 -d""" % (
                      self.kubectl_bin, secret
                  )
        jwt_token = LocalExec.cmd(cmd_command=jwt_cmd, result=True)
        if not jwt_token:
            RecodeLog.error(msg="生成kube-proxy token失败!")
            assert False
        control_params = [
            TMP_KUBERNETES_MASTER_BIN_DIR,
            TMP_KUBERNETES_MASTER_CONFIG_DIR,
            TMP_KUBERNETES_MASTER_SSL_DIR,
            params['CLUSTER_NAME'],
            params['KUBE_CONFIG'],
            KUBERNETES_APISERVER,
            jwt_token
        ]
        config_achieve = os.path.join(CMD_FILE_DIR, params['KUBE_CONFIG'])
        if not LocalExec.cmd_with_files(
                achieve_object=Achieve,
                achieve=config_achieve,
                params=control_params
        ):
            RecodeLog.error(msg="生成kube-proxy 配置文件失败！")
            assert False

    @staticmethod
    def kubeproxy_yaml(role):
        """
        :param role:
        :return:
        """
        if role == 'server':
            config_file = os.path.join(
                TMP_KUBERNETES_MASTER_CONFIG_DIR,
                'kube-proxy.conf'
            )
        else:
            config_file = os.path.join(
                TMP_KUBERNETES_NODE_CONFIG_DIR,
                'kube-proxy.conf'
            )
        if not Achieve.write_yaml(yaml_name=config_file, content=KUBEPROXY_CONFIG_DICT):
            RecodeLog.error(msg="写入配置文件:kube-proxy.conf，失败!")
            assert False

    def kube_proxy_config_rsync(self):
        """
        :return:
        """
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'kube-proxy.conf'),
                remotefile=os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.conf')
            )
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'kube-proxy.kubeconfig'),
                remotefile=os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.kubeconfig')
            )
            self.sftp.close()

        for value in KUBERNETES_NODE.values():
            if value in KUBERNETES_MASTER.values():
                continue
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_NODE_CONFIG_DIR, 'kube-proxy.conf'),
                remotefile=os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.conf')
            )
            self.sftp.sftp_put(
                localfile=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'kube-proxy.kubeconfig'),
                remotefile=os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.kubeconfig')
            )
            self.sftp.close()

    @staticmethod
    def kube_proxy_service():
        """
        :return:
        """
        exec_start = '''{0} --config={1} --v=2'''.format(
            os.path.join(KUBERNETES_BIN_DIR, 'kube-proxy'),
            os.path.join(KUBERNETES_CONFIG_DIR, 'kube-proxy.conf')
        )
        data = {
            'ExecStart': exec_start,
            "Restart": "always",
            "Type": "simple",
            "RestartSec": "10s"
        }
        achieve_src = os.path.join(TMP_SYSTEMCTL_DIR, 'kube-proxy.service')
        for path in [TMP_KUBERNETES_MASTER_DIR, TMP_KUBERNETES_NODE_DIR]:
            achieve = os.path.join(path, 'kube-proxy.service')
            shutil.copy(src=achieve_src, dst=achieve)
            if not Cf.write_achieve(
                    achieve=achieve,
                    sections='Service',
                    data=data,
                    upper=False
            ):
                RecodeLog.error(msg="启动脚本初始化失败：{0}".format(achieve))
                assert False

    def kuberproxy_control(self):
        """
        :return:
        """
        for value in get_cluster_list():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command='/bin/systemctl disable kube-proxy.service')
            self.sftp.remote_cmd(command='/bin/systemctl enable kube-proxy.service')
            self.sftp.remote_cmd(command='/bin/systemctl start kube-proxy.service')
            self.sftp.close()

    def package_decompression(self):
        """
        :return:
        """
        RecodeLog.info("=============开始本地解压安装kubernetes===============")
        # a = AchieveControl()
        check_file = os.path.join(TAG_FILE_DIR, 'kubernetes_package.success')
        if os.path.exists(check_file):
            return True
        self.server_decompression()
        self.node_decompression()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============本地解压安装完成kubernetes===============")
        return True

    def kubernetes_rsync(self):
        """
        :return:
        """
        RecodeLog.info("=============开始同步到其他节点kubernetes和kubelet===============")
        check_file = os.path.join(TAG_FILE_DIR, 'kubernetes_rsync.success')
        if os.path.exists(check_file):
            return True
        self.kubelet_config()
        # 生成kubernetes server启动脚本
        self.kubelet_service()
        self.kube_proxy_service()
        self.kubeproxy_yaml(role='server')
        self.kubeproxy_yaml(role='node')
        # 将kubernetes server拷贝到其他节点
        self.server_rsync_install()
        # 将kubernetes server拷贝到其他节点
        self.node_rsync_install()
        self.alias_kubelet()
        # 启动 k8s server
        self.enable_master_service()
        self.start_master_service()
        self.start_kubelet()
        self.pykube.login(pkey=os.path.join(TMP_KUBERNETES_MASTER_CONFIG_DIR, 'admin.kubeconfig'))
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============开始同步到其他节点kubernetes和kubelet===============")
        return True

    def kube_proxy_rsync(self):
        """
        :return:
        """
        RecodeLog.info("=============开始同步到其他节点kube-proxy===============")
        # a = AchieveControl()
        check_file = os.path.join(TAG_FILE_DIR, 'kubernetes_kubeproxy.success')
        if os.path.exists(check_file):
            return True
        time.sleep(60)
        self.tag_cluster()
        params = copy.deepcopy(KUBE_PROXY)
        self.kube_proxy_config(params=params)
        self.kubeproxy_yaml(role='server')
        self.kubeproxy_yaml(role='node')
        self.kube_proxy_config_rsync()
        self.kuberproxy_control()
        self.kubectl_apply()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============开始同步到其他节点kube-proxy===============")
        return True

    def write_flannel_yaml(self):
        """
        :return:
        """
        flannel_src = os.path.join(YAML_FILE_DIR, 'kube-flannel.yaml')
        flannel_dec = os.path.join(YAML_FILE_DIR, 'dec_kube-flannel.yaml')
        shutil.copy(src=flannel_src, dst=flannel_dec)
        Achieve.alter_achieve(achieve=flannel_dec, old_str='CNI_CONFIG', new_str=CNI_CONFIG_DIR)
        Achieve.alter_achieve(achieve=flannel_dec, old_str='CNI_VERSION', new_str=CNI_VERSION)
        Achieve.alter_achieve(achieve=flannel_dec, old_str='CLUSTER_RANGE', new_str=CLUSTER_ADDRESS)
        Achieve.alter_achieve(achieve=flannel_dec, old_str='CNI_IMAGE', new_str=IMAGE_DICT['CNI'])

    def write_coredns_yaml(self):
        """
        :return:
        """
        coredns_src = os.path.join(YAML_FILE_DIR, 'coredns.yaml')
        coredns_dec = os.path.join(YAML_FILE_DIR, 'dec_coredns.yaml')
        shutil.copy(src=coredns_src, dst=coredns_dec)
        Achieve.alter_achieve(achieve=coredns_dec, old_str='DNS_IP', new_str=CLUSTER_DNS)
        Achieve.alter_achieve(achieve=coredns_dec, old_str='CNI_IMAGE', new_str=IMAGE_DICT['coredns'])

    def kubectl_apply(self):
        command = "kubectl apply -f {0}".format(os.path.join(YAML_FILE_DIR, 'dec_kube-flannel.yaml'))
        LocalExec.cmd(cmd_command=command)
        command = "kubectl apply -f {0}".format(os.path.join(YAML_FILE_DIR, 'dec_coredns.yaml'))
        LocalExec.cmd(cmd_command=command)
