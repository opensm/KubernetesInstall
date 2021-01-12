# -*- coding: utf-8 -*-
from lib.BaseCommand import SSHFtp
from lib.FileCommand import Achieve
from lib.settings import *
from lib.setting.cni import *
from lib.Log import RecodeLog
from lib.dependent import class_tag_decorator


class CNIInstall:
    def __init__(self):
        created_dirs = [
            TMP_CNI_SSL_DIR,
            TMP_CNI_CONFIG_DIR,
            TMP_CNI_BIN_DIR,
            TMP_CNI_DIR
        ]
        checked_dirs = [
            ABS_CNI_PACKAGE
        ]
        Achieve.check_dirs(dir_list=created_dirs, create=True)
        Achieve.check_dirs(dir_list=checked_dirs, create=False)
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)

    @staticmethod
    def cni_install():
        """
        :return:
        """
        # 解压文件
        if not Achieve.tar_decompression(
                achieve=ABS_CNI_PACKAGE,
                target_path=TMP_CNI_BIN_DIR
        ):
            RecodeLog.error(msg="解压文件失败：{0}!".format(ABS_CNI_PACKAGE))
            assert False
        RecodeLog.info(msg="cni 安装成功，{0}".format(TMP_CNI_BIN_DIR))

    def rsync_install(self):
        """
        :return:
        """
        cluster_list = list()
        for value in KUBERNETES_MASTER.values():
            if value in cluster_list:
                continue
            cluster_list.append(value)

        for value in KUBERNETES_NODE.values():
            if value in cluster_list:
                continue
            cluster_list.append(value)
        # 传输文件
        for host in cluster_list:
            self.sftp.host = host
            self.sftp.connect()
            self.sftp.sftp_put_dir(local_dir=TMP_CNI_DIR, remote_dir=CNI_HOME)
            self.sftp.remote_cmd(command='chmod 760 {0}'.format(os.path.join(CNI_BIN_DIR, '*')))
            RecodeLog.info(msg="远程同步CNI程序到：{0},成功！".format(host))
            self.sftp.close()

    @class_tag_decorator
    def run_cni(self):
        """
        :return:
        """
        self.cni_install()
        self.rsync_install()
