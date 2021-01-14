# -*- coding: utf-8 -*-
import shutil
from lib.BaseCommand import SSHFtp, LocalExec
from lib.FileCommand import Achieve
from lib.Log import RecodeLog
from lib.settings import *
from lib.dependent import class_tag_decorator
from lib.setting.base import TMP_PACKAGE_PATH, TMP_SYSTEMCTL_DIR, SYSTEMCTL_DIR
from lib.setting.keepalived import *


class KeepalivedInstall(object):

    def __init__(self):
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)
        self.__tmp_install_dir = os.path.join(
            TMP_PACKAGE_PATH, 'keepalived'
        )
        checked_dirs = [
            ABS_KEEPALIVED_PACKAGE
        ]
        Achieve.check_dirs(dir_list=checked_dirs)

    @staticmethod
    def install(sftp):
        """
        :param sftp:
        :return:
        """
        if not isinstance(sftp, SSHFtp):
            raise TypeError('输入类型错误！')
        remote_source = os.path.join(
            REMOTE_TMP_DIR,
            'install_keepalived',
            'install_keepalived.sh'
        )
        command = 'bash {0} {1} {2}'.format(
            remote_source,
            os.path.join(REMOTE_TMP_DIR, 'install_keepalived', 'resource'),
            KEEPALIVED_PACKAGE
        )
        sftp.sftp_put_dir(
            os.path.join(TMP_PACKAGE_PATH, 'install_keepalived'),
            os.path.join(REMOTE_TMP_DIR, 'install_keepalived')
        )
        sftp.remote_cmd(command=command)
        RecodeLog.info(msg="主机:{0},远程安装:{1},成功！".format(sftp.host, command))

    @staticmethod
    def write_keepalive_conf(src_file, host, ifname='eth0', rename=None):
        """
        :param src_file:
        :param host:
        :param ifname:
        :param rename:
        :return:
        """

        if not os.path.exists(src_file):
            RecodeLog.error(msg="文件不存在：{0}".format(src_file))
            assert False
        if rename:
            dsc = rename
        else:
            dsc = "{1}_{0}".format(src_file, host)
        shutil.copy(src_file, dsc)
        # 修改网卡
        if not Achieve.alter_achieve(
                achieve=dsc,
                old_str='{{ interface }}',
                new_str=ifname,
                matching='interface'
        ):
            RecodeLog.error(
                msg="修改文件：{0},内容失败,修改内容：{1},为:{2}".format(
                    dsc,
                    '{{ interface }}',
                    ifname
                ))
            assert False
        # 修改端口
        if not Achieve.alter_achieve(
                achieve=dsc,
                old_str='{{ ADDRESS }}',
                new_str="https://{0}:{1}".format(host, KUBERNETES_PORT)
        ):
            RecodeLog.error(
                msg="修改文件：{0},替换文件内容失败：{1},{2}".format(
                    dsc,
                    '{{ ADDRESS }}',
                    "https://{0}:{1}".format(host, KUBERNETES_PORT)
                )
            )
            assert False

            # 修改端口
        if not Achieve.alter_achieve(
                achieve=dsc,
                old_str='{{ VIP }}',
                new_str=KUBERNETES_VIP
        ):
            RecodeLog.error(
                msg="修改文件：{0},替换文件内容失败：{1},{2}".format(
                    dsc,
                    '{{ VIP }}',
                    KUBERNETES_VIP
                )
            )
            assert False

    def start_keepalived(self):
        """
        :param
        status:
        :return:
        """
        for value in KUBERNETES_MASTER.values():
            self.sftp.host = value
            self.sftp.connect()
            self.sftp.remote_cmd(command="/bin/systemctl daemon-reload")
            self.sftp.remote_cmd(command="/bin/systemctl disable keepalived && /bin/systemctl enable keepalived")
            self.sftp.remote_cmd(command="/bin/systemctl start keepalived")
            self.sftp.close()

    def binary_build(self):
        """
        :return:
        """
        binary_build_shell = os.path.join(
            TMP_PACKAGE_PATH,
            'install_keepalived',
            'binary_build.sh'
        )
        LocalExec.cmd(cmd_command="bash {0} {1} {2} {3}".format(
            binary_build_shell,
            TMP_PACKAGE_PATH,
            KEEPALIVED_PACKAGE,
            self.__tmp_install_dir
        ))
        shutil.copy(
            os.path.join(TMP_SYSTEMCTL_DIR, 'keepalived.service'),
            self.__tmp_install_dir
        )

    def remote_install(self):
        """
        :return:
        """
        tmp_config_dir = os.path.join(
            TMP_PACKAGE_PATH,
            'install_keepalived'
        )
        master_keepalive_config = os.path.join(
            tmp_config_dir,
            'master_keepalived.conf'
        )
        slave_keepalive_config = os.path.join(
            tmp_config_dir,
            'slave_keepalived.conf'
        )
        tmp_keepalive_script = os.path.join(
            tmp_config_dir,
            'ingress_health_check.py'
        )
        keepalived_config = '/etc/keepalived/keepalived.conf'
        keepalive_script = '/etc/keepalived/ingress_health_check.py'
        master_list = KUBERNETES_MASTER.values()
        for i in range(0, len(master_list)):
            node_keepalived_conf = os.path.join(
                tmp_config_dir,
                '{0}_keepalived.conf'.format(master_list[i])
            )
            # 判断节点性质
            if i < 1:
                keepalived_dict = {
                    'host': master_list[i],
                    'ifname': IFNAME,
                    'src_file': master_keepalive_config,
                    'rename': node_keepalived_conf
                }
            else:
                keepalived_dict = {
                    'host': master_list[i],
                    'ifname': IFNAME,
                    'src_file': slave_keepalive_config,
                    'rename': node_keepalived_conf
                }
            # 写入keepalived配置文件
            self.write_keepalive_conf(**keepalived_dict)
            # 拷贝配置文件到安装目录
            shutil.copy(src=node_keepalived_conf, dst=self.__tmp_install_dir)
            shutil.copy(src=tmp_keepalive_script, dst=self.__tmp_install_dir)
            # 链接并拷贝配置到远程端
            self.sftp.host = master_list[i]
            self.sftp.connect()
            self.sftp.sftp_put_dir(local_dir=self.__tmp_install_dir, remote_dir=KEEPALIVED_HOME)
            self.sftp.remote_cmd(command="[[ -d /etc/keepalived ]] || mkdir -pv /etc/keepalived")
            self.sftp.remote_cmd(command="ln -sf {0} /usr/sbin/ && chmod 777 /usr/sbin/keepalived".format(
                os.path.join(KEEPALIVED_HOME, 'sbin', '*')
            ))
            self.sftp.remote_cmd(command="ln -sf {0} /usr/bin/".format(
                os.path.join(KEEPALIVED_HOME, 'bin', '*')
            ))

            self.sftp.remote_cmd(
                command='ln -sf {0} {1}'.format(
                    os.path.join(
                        KEEPALIVED_HOME,
                        '{0}_keepalived.conf'.format(master_list[i])
                    ),
                    keepalived_config
                )
            )
            self.sftp.remote_cmd(
                command='ln -sf {0} {1}'.format(
                    os.path.join(KEEPALIVED_HOME, 'keepalived.service'),
                    SYSTEMCTL_DIR
                )
            )
            self.sftp.remote_cmd(
                command='ln -sf {0} {1}'.format(
                    os.path.join(KEEPALIVED_HOME, 'ingress_health_check.py'),
                    keepalive_script
                )
            )
            self.sftp.close()

    @class_tag_decorator
    def run_keepalive(self):
        """
        :return:
        """
        self.binary_build()
        self.remote_install()
        self.start_keepalived()
