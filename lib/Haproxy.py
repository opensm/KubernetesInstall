# -*- coding: utf-8 -*-
import copy
import os
import shutil
from lib.BaseCommand import SSHFtp, LocalExec
from lib.Log import RecodeLog
from lib.FileCommand import Achieve
from lib.setting.haproxy import HAPROXY_PACKAGE, HAPROXY_HOME
from lib.settings import AUTHENTICATION, REMOTE_TMP_DIR, KUBERNETES_MASTER
from lib.setting.base import TMP_PACKAGE_PATH, TAG_FILE_DIR


class HaProxyInstall:
    def __init__(self):
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)
        self.__tmp_install_dir = os.path.join(
            TMP_PACKAGE_PATH, 'haproxy'
        )

    @staticmethod
    def install(sftp):
        """
        :return:
        """
        if not isinstance(sftp, SSHFtp):
            raise TypeError("输入类型错误！")
        exec_dir = os.path.join(
            REMOTE_TMP_DIR, 'install_haproxy'
        )
        command = 'bash {0} {1} {2}'.format(
            os.path.join(
                exec_dir, 'install_haproxy.sh'
            ),
            os.path.join(exec_dir, 'resource'),
            HAPROXY_PACKAGE
        )
        sftp.remote_cmd(command=command)
        RecodeLog.info(msg="远程部署成功：{0}".format(command))

    def binary_build(self):
        """
        :return:
        """
        binary_build_shell = os.path.join(
            TMP_PACKAGE_PATH,
            'install_haproxy',
            'binary_build.sh'
        )
        LocalExec.cmd(cmd_command="bash {0} {1} {2} {3}".format(
            binary_build_shell,
            TMP_PACKAGE_PATH,
            HAPROXY_PACKAGE,
            self.__tmp_install_dir
        ))

    def remote_install(self):
        """
        :return:
        """
        local_resource_dir = os.path.join(
            TMP_PACKAGE_PATH,
            'install_haproxy'
        )
        local_haproxy_config = os.path.join(
            local_resource_dir,
            'conf',
            'haproxy.cfg'
        )
        tmp_config_dir = os.path.join(
            self.__tmp_install_dir,
            'haproxy.cfg'
        )
        local_haproxy_systemctl = os.path.join(local_resource_dir, 'haproxy.service')

        shutil.copy(local_haproxy_config, tmp_config_dir)
        shutil.copy(local_haproxy_systemctl, tmp_config_dir)
        haproxy_config = '/etc/haproxy/haproxy.cfg'
        master_list = KUBERNETES_MASTER.values()
        for i in range(0, len(master_list)):
            Achieve.write_file(
                achieve=tmp_config_dir,
                content="\n  server k8s_api_{0} {1}:6443 check".format(i, master_list[i]),
                mode='a'
            )
        for i in range(0, len(master_list)):
            auth = copy.deepcopy(AUTHENTICATION)
            auth['host'] = master_list[i]
            self.sftp.host = master_list[i]
            self.sftp.connect()
            self.sftp.sftp_put_dir(local_dir=self.__tmp_install_dir, remote_dir=HAPROXY_HOME)
            self.sftp.sftp_put(localfile=tmp_config_dir, remotefile=haproxy_config)
            self.sftp.remote_cmd(command="[[ ! -d /etc/haproxy ]] || mkdir -pv /etc/haproxy")
            self.sftp.remote_cmd(command="ln -sf {0} /usr/sbin/".format(
                os.path.join(HAPROXY_HOME, 'sbin', '*')
            ))
            self.sftp.remote_cmd(
                command='ln -sf {0} {1}'.format(
                    os.path.join(HAPROXY_HOME, 'haproxy.cfg'),
                    haproxy_config
                )
            )
            self.install(sftp=self.sftp)
            self.sftp.close()
            RecodeLog.info(msg="Haproxy传输文件到{0}主机，成功!".format(master_list[i]))

    def start_haproxy(self):
        """
        :return:
        """
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command="/bin/systemctl daemon-reload")
            self.sftp.remote_cmd(command=" /bin/systemctl disable haproxy && /bin/systemctl enable haproxy")
            self.sftp.remote_cmd(command="/bin/systemctl start haproxy")
            self.sftp.close()
            RecodeLog.info(msg="主机:{0},haproxy启动成功，并设置开机启动".format(value))

    def run_haproxy(self):
        """
        :return:
        """
        RecodeLog.info("=============开始执行haproxy部分===============")
        # a = AchieveControl()
        check_file = os.path.join(TAG_FILE_DIR, 'haproxy.success')
        if os.path.exists(check_file):
            RecodeLog.info("=============已存在完成状态文件，跳过执行haproxy部分===============")
            return True
        self.binary_build()
        self.remote_install()
        self.start_haproxy()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============执行完成haproxy部分===============")
        return True
