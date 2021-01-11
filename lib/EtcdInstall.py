# -*- coding: utf-8 -*-
import shutil
from lib.Log import RecodeLog
from lib.BaseCommand import SSHFtp
from lib.FileCommand import Achieve
from lib.OpenSSlControl import Cf
from lib.setting.etcd import *
from lib.settings import CURRENT_PATH, ETCD_CLUSTER_LIST, AUTHENTICATION
from lib.setting.openssl import OPENSSL_TMP_DIR
from lib.setting.base import TMP_SYSTEMCTL_DIR, SYSTEMCTL_DIR


class EtcdInstall:

    def __init__(self):
        created_dirs = [
            TMP_ETCD_SSL_DIR,
            TMP_ETCD_CONFIG_DIR,
            TMP_ETCD_BIN_DIR
        ]
        checked_dirs = [
            ABS_ETCD_PACKAGE
        ]
        Achieve.check_dirs(dir_list=created_dirs, create=True)
        Achieve.check_dirs(dir_list=checked_dirs, create=False)
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)

    def install(self):
        """
        :return:
        """

        # 解压文件
        if not Achieve.tar_decompression(
                achieve=ABS_ETCD_PACKAGE,
                target_path=os.path.join(CURRENT_PATH, 'package')
        ):
            RecodeLog.error(msg="解压文件失败：{0}!".format(ABS_ETCD_PACKAGE))
            assert False
        tar_decompressed_bin = ABS_ETCD_PACKAGE.replace('.tar.gz', '')
        proc_list = ['etcdctl', 'etcd']
        try:
            if not os.path.exists(tar_decompressed_bin):
                raise Exception("解压文件不存在目录:{0}".format(tar_decompressed_bin))
            for proc in proc_list:
                shutil.copy(src=os.path.join(tar_decompressed_bin, proc), dst=TMP_ETCD_BIN_DIR)
            RecodeLog.info(msg="etcd 安装成功，{0}".format(TMP_ETCD_BIN_DIR))
        except Exception as error:
            RecodeLog.info(msg="etcd 安装失败，{0},原因：{1}".format(TMP_ETCD_BIN_DIR, error))
            assert False

        # 拷贝ssl文件到临时安装目录
        try:
            for ssl in ETCD_SSL_LIST:
                ssl_abs = os.path.join(OPENSSL_TMP_DIR, 'etcd', ssl)
                if not Achieve.check_achieve(achieve=TMP_ETCD_SSL_DIR):
                    raise Exception("文件不存在:{0}".format(ssl_abs))
                shutil.copy(src=ssl_abs, dst=TMP_ETCD_SSL_DIR)
                RecodeLog.info(msg="拷贝:{0},到{1},成功！".format(ssl, TMP_ETCD_SSL_DIR))
        except Exception as error:
            RecodeLog.error(msg="拷贝失败，原因:{0}".format(error))
            assert False
        initial_cluster = ""
        for x in range(0, len(ETCD_CLUSTER_LIST)):
            initial_cluster = "%s,etcd%02d=https://%s:2380" % (initial_cluster, (x + 1), ETCD_CLUSTER_LIST[x])
        for i in range(0, len(ETCD_CLUSTER_LIST)):
            config_achieve = os.path.join(TMP_ETCD_CONFIG_DIR, "config_{0}.yaml".format(ETCD_CLUSTER_LIST[i]))
            config_data = ETCD_CONFIG_DICT
            config_data['name'] = "etcd%02d" % (i + 1)
            config_data['listen-peer-urls'] = "https://{0}:2380".format(ETCD_CLUSTER_LIST[i])
            config_data['listen-client-urls'] = "https://{0}:2379,https://127.0.0.1:2379".format(ETCD_CLUSTER_LIST[i])
            config_data['cors'] = None
            config_data['initial-advertise-peer-urls'] = "https://{0}:2380".format(ETCD_CLUSTER_LIST[i])
            config_data['advertise-client-urls'] = "https://{0}:2379".format(ETCD_CLUSTER_LIST[i])
            config_data['initial-cluster'] = initial_cluster.lstrip(',').rstrip(',')
            if not Achieve.write_yaml(yaml_name=config_achieve, content=config_data):
                assert False
        if not self.etcd_service():
            assert False

    def etcd_service(self):
        """
        :return:
        """
        exec_start = "{0} --config-file={1}".format(
            os.path.join(ETCD_BIN_DIR, 'etcd'),
            os.path.join(ETCD_CONFIG_DIR, 'config.yaml')
        )
        data = {
            'ExecStart': exec_start,
            "Type": "notify",
            "Restart": "on-failure",
            "RestartSec": 10,
            "LimitNOFILE": 65536
        }
        source_achieve = os.path.join(TMP_SYSTEMCTL_DIR, 'etcd.service')
        dst_achieve = os.path.join(TMP_ETCD_DIR, 'etcd.service')

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

    def rsync_install(self):
        """
        :return:
        """
        command1 = "chmod 700 {0}".format(
            os.path.join(ETCD_BIN_DIR, '*')
        )
        command2 = "[[ -f {0} ]] || rm -f {0}".format(
            os.path.join(ETCD_CONFIG_DIR, 'config.yaml')
        )
        command4 = "ln -s {0} {1}".format(
            os.path.join(ETCD_HOME, 'etcd.service'),
            SYSTEMCTL_DIR
        )
        for endpoint in ETCD_CLUSTER_LIST:
            command3 = "[[ ! -f {1} ]] || rm -f {1} && ln -s {0} {1}".format(
                os.path.join(
                    ETCD_CONFIG_DIR,
                    "config_{0}.yaml".format(endpoint),
                ),
                os.path.join(
                    ETCD_CONFIG_DIR,
                    'config.yaml'
                ),
            )
            self.sftp.host = endpoint
            self.sftp.connect()
            self.sftp.sftp_put_dir(local_dir=TMP_ETCD_DIR, remote_dir=ETCD_HOME)
            self.sftp.remote_cmd(command=command1)
            RecodeLog.info("远程主机:{0},执行:{1},成功！".format(endpoint, command1))
            self.sftp.remote_cmd(command=command2)
            RecodeLog.info("远程主机:{0},执行:{1},成功！".format(endpoint, command2))
            self.sftp.remote_cmd(command=command3)
            RecodeLog.info("远程主机:{0},执行:{1},成功！".format(endpoint, command3))
            self.sftp.remote_cmd(command=command4)
            RecodeLog.info("远程主机:{0},执行:{1},成功！".format(endpoint, command4))
            self.sftp.close()

    def etcd_control(self):
        """
        :return:
        """
        # r = RemoteSSHCommand()
        for value in ETCD_CLUSTER_LIST:
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command="/bin/systemctl daemon-reload")
            self.sftp.remote_cmd(command="/bin/systemctl disable etcd && /bin/systemctl enable etcd")
            self.sftp.remote_cmd(command="nohup /bin/systemctl start --now  etcd >/dev/null &")
            self.sftp.close()

    def run_etcd(self):
        """
        :return:
        """
        RecodeLog.info("=============开始执行etcd部分===============")
        # a = AchieveControl()
        check_file = os.path.join(CURRENT_PATH, 'tmp', 'etcd.success')
        if os.path.exists(check_file):
            RecodeLog.info("=============已存在完成状态文件，跳过执行etcd部分===============")
            return True
        self.install()
        self.rsync_install()
        self.etcd_control()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============执行完成etcd部分===============")
        return True
