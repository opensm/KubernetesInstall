# -*- coding: utf-8 -*-
from lib.BaseCommand import *
from lib.FileCommand import Achieve
from lib.Log import *
from lib.settings import *
from lib.setting.base import TAG_FILE_DIR, TMP_PACKAGE_PATH
import os
import shutil

sftp = SSHFtp()
sftp.setLoginVariable(data=AUTHENTICATION)


def tag_decorator(tag):
    def rapTheFunction(*args, **kwargs):
        check_file = os.path.join(TAG_FILE_DIR, '{0}.success'.format(getattr(tag, '__name__')))
        if os.path.exists(check_file):
            RecodeLog.info(msg="{0} 已经执行，跳过执行!".format(getattr(tag, '__name__')))
            return None
        else:
            test_ping()
            RecodeLog.info("=============开始执行:{0}===============".format(getattr(tag, '__name__')))
            tag()
            RecodeLog.info("=============执行完成:{0}===============".format(getattr(tag, '__name__')))
            Achieve.touch_achieve(check_file)
            return None

    return rapTheFunction


def class_tag_decorator(tag):
    def rapTheFunction(self):
        check_file = os.path.join(TAG_FILE_DIR, '{0}.success'.format(getattr(tag, '__name__')))
        if os.path.exists(check_file):
            RecodeLog.info(msg="{0} 已经执行，跳过执行!".format(getattr(tag, '__name__')))
            return None
        else:
            test_ping()
            RecodeLog.info("=============开始执行:{0}===============".format(getattr(tag, '__name__')))
            tag(self)
            RecodeLog.info("=============执行完成:{0}===============".format(getattr(tag, '__name__')))
            Achieve.touch_achieve(check_file)
            return None

    return rapTheFunction


def check_env():
    if len(KUBERNETES_MASTER.values()) == 1 and KUBERNETES_MASTER.values()[0] != KUBERNETES_VIP:
        RecodeLog.error(msg="单节点中请将VPN与masterIP设置一致！")
        assert False
    if len(KUBERNETES_MASTER.values()) > 1 and KUBERNETES_VIP in KUBERNETES_MASTER.values():
        RecodeLog.error(msg="K8S集群不能将MasterIP作为VIP！")
        assert False
    if len(KUBERNETES_NODE.values()) == 0:
        RecodeLog.error(msg="K8S集群Node为空！")
        assert False

    plus_cluster = list(set(KUBERNETES_MASTER.values()).intersection(set(KUBERNETES_NODE.values())))
    if len(plus_cluster) > 0:
        RecodeLog.info(msg="集群中存在Master与Node交叉使用主机的情况，请检查!")
        assert False


def write_hosts():
    hosts = "/etc/hosts"
    k8s_hosts = "/etc/hosts.kube"
    shutil.copy(src=hosts, dst=k8s_hosts)
    cluster_list = KUBERNETES_MASTER.copy()
    cluster_list.update(KUBERNETES_NODE)
    for key, value in cluster_list.items():
        write_hostname(host=value, hostname=key)
        if not Achieve.write_hosts(ipaddr=value, domain=key, hosts=k8s_hosts):
            RecodeLog.error(msg="写入失败/etc/hosts,{0} {1}".format(key, value))
            assert False
        else:
            RecodeLog.info(msg="成功写入/etc/hosts,{0} {1}".format(key, value))


def write_hostname(host, hostname):
    """
    :param host:
    :param hostname:
    :return:
    """

    command = """echo '{0}' > /etc/hostname""".format(hostname)
    sftp.host = host
    sftp.connect()
    sftp.remote_cmd(command=command)
    sftp.close()
    RecodeLog.info(msg="写入主机名称成功！{0}".format(command))


def rsync_host():
    write_hosts()
    hosts = "/etc/hosts"
    k8s_hosts = "/etc/hosts.kube"
    host_list = get_cluster_list()
    for host in host_list:
        sftp.host = host
        sftp.connect()
        sftp.sftp_put(
            localfile=k8s_hosts,
            remotefile=hosts
        )
        sftp.close()


def get_cluster_list():
    cluster_list = list()
    for value in KUBERNETES_MASTER.values():
        if value in cluster_list:
            continue
        cluster_list.append(value)

    for value in KUBERNETES_NODE.values():
        if value in cluster_list:
            continue
        cluster_list.append(value)

    return cluster_list


@tag_decorator
def dependent():
    # 判断当前安装目录是否存在主目录，存在就将其移走

    # check_file = os.path.join(CURRENT_PATH, 'tmp', 'dependent.success')
    # if os.path.exists(check_file):
    #     RecodeLog.info("=============已存在完成状态文件，跳过执行dependent部分===============")
    #     return True
    cluster_list = get_cluster_list()
    for host in cluster_list:
        sftp.host = host
        sftp.connect()
        sftp.sftp_put_dir(
            local_dir=os.path.join(TMP_PACKAGE_PATH, 'install_docker'),
            remote_dir=REMOTE_TMP_DIR
        )
        sftp.sftp_put_dir(
            local_dir=os.path.join(TMP_PACKAGE_PATH, 'upgrade-kernel'),
            remote_dir=REMOTE_TMP_DIR
        )
        sftp.close()
    # Achieve.touch_achieve(achieve=check_file)
    rsync_host()
    return True


@tag_decorator
def kernel_update():
    # RecodeLog.info("=============开始执行kernel_update部分===============")
    # check_file = os.path.join(TAG_FILE_DIR, 'kernel_update.success')
    # if os.path.exists(check_file):
    #     RecodeLog.info("=============已存在完成状态文件，跳过执行kernel_update部分===============")
    #     return True
    command = "bash {0}".format(os.path.join(
        REMOTE_TMP_DIR, 'upgrade-kernel.sh'
    ))
    cluster_list = get_cluster_list()
    for host in cluster_list:
        sftp.host = host
        sftp.connect()
        sftp.remote_cmd(command=command)
        sftp.close()
        RecodeLog.info(msg="主机:{0},执行成功:{1}".format(host, command))
    # Achieve.touch_achieve(achieve=check_file)
    # reboot = ""
    # while reboot.upper() not in ['YES', 'NO', 'Y', 'N']:
    #     reboot = raw_input("注意！！！！！\nkernel升级完成,是否现在重启集群全部主机？yes/YES or NO/no:")
    #     if not isinstance(reboot, str):
    #         print("输入类型错误")
    #         assert False
    # if reboot.upper() == "YES" or reboot.upper() == "Y":
    #     # 其他主机重启
    #     for host in cluster_list:
    #         if LocalExec.check_ip_same(host, IFNAME):
    #             continue
    #         sftp.host = host
    #         sftp.connect()
    #         sftp.remote_cmd(command='reboot')
    #         RecodeLog.info(msg="主机:{0},执行成功:reboot".format(host))
    #         sftp.close()
    #     # 重启本机
    #     for host in cluster_list:
    #         if not LocalExec.check_ip_same(host, IFNAME):
    #             continue
    #         LocalExec.cmd(cmd_command="reboot")
    # else:
    #     RecodeLog.info(msg="请操作完成之后自行重启集群主机")
    #     assert False
    # Achieve.touch_achieve(achieve=check_file)
    return True


@tag_decorator
def docker_install():
    # RecodeLog.info("=============开始执行docker_install部分===============")
    # check_file = os.path.join(TAG_FILE_DIR, 'docker_install.success')
    # if os.path.exists(check_file):
    #     RecodeLog.info("=============已存在完成状态文件，跳过执行docker_install部分===============")
    #     return True
    cluster_list = get_cluster_list()
    command = "bash {0}".format(
        os.path.join(
            REMOTE_TMP_DIR, 'install_docker.sh'
        ))
    for host in cluster_list:
        sftp.host = host
        sftp.connect()
        sftp.remote_cmd(command=command)
        sftp.close()
        RecodeLog.info(msg="主机:{0},执行成功:{1}".format(host, command))

    # Achieve.touch_achieve(achieve=check_file)


def test_ping():
    RecodeLog.info(msg="开始测试各个主机的联通性！")
    cluster_list = get_cluster_list()
    for host in cluster_list:
        command = "echo 'Test connect to {0}'".format(host)
        sftp.host = host
        sftp.connect()
        sftp.remote_cmd(command=command)
        sftp.close()
        RecodeLog.info(msg="测试连通性成功:{0},执行成功:{1}".format(host, command))


__all__ = [
    'dependent',
    'kernel_update',
    'docker_install',
    'check_env',
    'get_cluster_list',
    'tag_decorator',
    'class_tag_decorator',
    'test_ping'
]
