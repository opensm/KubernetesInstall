# -*- coding: utf-8 -*-
import copy
import shutil
from lib.BaseCommand import SSHFtp
from lib.FileCommand import Achieve
from lib.Log import RecodeLog
from lib.settings import *
from lib.setting.base import TMP_PACKAGE_PATH, TAG_FILE_DIR
from lib.setting.keepalived import KEEPALIVED_PACKAGE


class KeepalivedInstall(object):

    def __init__(self):
        self.sftp = SSHFtp()
        self.sftp.setLoginVariable(data=AUTHENTICATION)

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
        sftp.sftp_put(REMOTE_TMP_DIR, TMP_PACKAGE_PATH)
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
            shutil.copy(src_file, rename)
        else:
            shutil.copy(src_file, "{1}_{0}".format(src_file, host))
        # 修改网卡
        if not Achieve.alter_achieve(
                achieve=src_file,
                old_str='{{ interface }}',
                new_str=ifname,
                matching='interface'
        ):
            RecodeLog.error(
                msg="修改文件：{0},内容失败,修改内容：{1},为:{2}".format(
                    src_file,
                    '{{ interface }}',
                    ifname
                ))
            return False
        # 修改端口
        if not Achieve.alter_achieve(
                achieve=src_file,
                old_str='{{ PORT }}',
                new_str=KUBERNETES_PORT
        ):
            RecodeLog.error(
                msg="修改文件：{0},替换文件内容失败：{1},{2}".format(
                    src_file,
                    '{{ PORT }}',
                    KUBERNETES_PORT
                )
            )
            return False
        else:
            return True

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

    def remote_install(self):
        """
        :return:
        """
        tmp_config_dir = os.path.join(
            TMP_PACKAGE_PATH,
            'install_keepalived',
            'conf'
        )
        tmp_resource_dir = os.path.join(
            TMP_PACKAGE_PATH,
            'install_keepalived',
            'resource'
        )
        master_keepalive_config = os.path.join(
            tmp_config_dir,
            'master_keepalived.conf'
        )
        slave_keepalive_config = os.path.join(
            tmp_config_dir,
            'slave_keepalived.conf'
        )
        keepalived_config = '/etc/keepalived/keepalived.conf'
        master_list = KUBERNETES_MASTER.values()
        for i in range(0, len(master_list)):
            # 定义变量
            auth = copy.deepcopy(AUTHENTICATION)
            auth['host'] = master_list[i]
            # 判断节点性质
            if i < 1:
                keepalived_dict = {
                    'host': master_list[i],
                    'ifname': IFNAME,
                    'src_file': master_keepalive_config,
                    'rename': os.path.join(
                        tmp_resource_dir,
                        '{0}_keepalived.conf'.format(master_list[i])
                    )
                }
            else:
                keepalived_dict = {
                    'host': master_list[i],
                    'ifname': IFNAME,
                    'src_file': slave_keepalive_config,
                    'rename': os.path.join(
                        tmp_resource_dir,
                        '{0}_keepalived.conf'.format(master_list[i])
                    )
                }
            # 写入keepalived配置文件
            if not self.write_keepalive_conf(**keepalived_dict):
                RecodeLog.error(
                    msg="修改配置文件失败,  {0}_keepalived.conf!".format(
                        master_list[i]
                    )
                )
                assert False
            # 链接并拷贝配置到远程端
            self.sftp.host = master_list[i]
            self.sftp.connect()
            self.sftp.sftp_put(
                localfile=os.path.join(
                    tmp_resource_dir,
                    '{0}_keepalived.conf'.format(master_list[i])
                ), remotefile=keepalived_config
            )
            # 执行安装
            self.install(sftp=self.sftp)
            self.sftp.close()

    def run_keepalive(self):
        """
        :return:
        """
        RecodeLog.info("=============开始执行keepalived部分===============")
        check_file = os.path.join(TAG_FILE_DIR, 'keepalived.success')
        if os.path.exists(check_file):
            RecodeLog.info("=============已存在完成状态文件，跳过执行keepalived部分===============")
            return True
        self.remote_install()
        self.start_keepalived()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============执行完成keepalived部分===============")
        return True
