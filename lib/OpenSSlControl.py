# -*- coding: utf-8 -*-
import time
import shutil
import platform
from lib.BaseCommand import *
from lib.FileCommand import Achieve
from lib.settings import *
from lib.setting.base import CMD_FILE_DIR
from lib.Log import *

if int(platform.python_version().strip(".")[0]) < 3:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser


class ReConfigParser(ConfigParser):
    def __init__(self, defaults=None):
        ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr


class OpenSSLControl:
    def __init__(self):
        self.cf = ConfigParserControl()
        if not isinstance(KUBERNETES_NODE, dict) and isinstance(KUBERNETES_MASTER, dict):
            RecodeLog.error(msg="请检查:KUBERNETES_MASTER,KUBERNETES_NODE的数据类型，必须是dict")
            assert False

    def make_openssl_config(self, sections, all_instance, all_dns_list):
        """
        :param sections:
        :param all_instance:
        :param all_dns_list:
        :return:
        """
        # 配置文件生成
        config_file = os.path.join(OPENSSL_CONFIG_DIR, 'openssl.conf')
        if not os.path.exists(config_file):
            RecodeLog.error(msg="{0} is not exist!".format(config_file))
            assert False
        all_instance_dict = dict()
        if len(all_instance) == 0:
            RecodeLog.error(msg="获取到的instance列表为空，请检查")
            assert False
        for i in range(0, len(all_dns_list)):
            all_instance_dict['DNS.{0}'.format(i)] = all_dns_list[i]
        for i in range(0, len(all_instance)):
            all_instance_dict['IP.{0}'.format(i)] = all_instance[i]

        if self.cf.write_achieve(achieve=config_file, sections=sections, data=all_instance_dict):
            RecodeLog.info(msg="写入集群IP列表成功:{0},模块:{1}".format(config_file, sections))
        else:
            RecodeLog.error(msg="写入集群IP列表失败:{0},模块:{1}".format(config_file, sections))
            assert False

    def write_openssl_config(self):
        cluster_list = list()
        etcd_list = list()
        # 添加本地主机
        cluster_list.append('127.0.0.1')
        cluster_list.append('10.96.0.1')
        cluster_dns_list = [
            'kubernetes',
            'kubernetes.default',
            'kubernetes.default.svc',
            'kubernetes.default.svc.cluster.local',
            'localhost'
        ]
        etcd_dns_list = [
            'localhost'
        ]
        etcd_list.extend(ETCD_CLUSTER_LIST)
        etcd_list.append('127.0.0.1')
        # 获取两个类型的主机中的所有主机的列表
        kubernetes_master_list = [x for x in KUBERNETES_MASTER.values()]
        kubernetes_node_list = [x for x in KUBERNETES_NODE.values()]
        # 汇总集群所有主机
        cluster_list.extend(ETCD_CLUSTER_LIST)
        cluster_list.extend(kubernetes_master_list)
        cluster_list.extend(kubernetes_node_list)
        cluster_list.append(KUBERNETES_VIP)
        # 去重集群主机
        cluster_list = list(set(cluster_list))
        # 从临时目录拷贝配置文件
        tmp_config = os.path.join(CURRENT_PATH, 'setting', 'openssl.conf')

        if not os.path.exists(OPENSSL_CONFIG_DIR):
            os.makedirs(OPENSSL_CONFIG_DIR)

        try:
            shutil.copy(src=tmp_config, dst=OPENSSL_CONFIG_DIR)
            RecodeLog.info(msg="拷贝文件:{0},到:{1},成功".format(tmp_config, OPENSSL_CONFIG_DIR))
        except Exception as error:
            RecodeLog.error(msg="拷贝文件:{0},到:{1},失败,原因:{2}".format(tmp_config, OPENSSL_CONFIG_DIR, error))
            assert False
        # 生成openssl 配置的集群列表
        self.make_openssl_config(all_instance=cluster_list, all_dns_list=cluster_dns_list, sections='alt_names_cluster')
        # 生成openssl etcd配置列表
        self.make_openssl_config(all_instance=etcd_list, all_dns_list=etcd_dns_list, sections='alt_names_etcd')

    @staticmethod
    def format_openssl_cmd(exec_bin, sub_command, profix="-", *args, **kwargs):
        """
        :param exec_bin:
        :param sub_command:
        :param profix:
        :param args:
        :param kwargs:
        :return:
        """
        if not os.path.exists(exec_bin):
            RecodeLog.error(msg="可执行程序：{0}，不存在".format(exec_bin))
            assert False
        params = ""
        for value in args:
            params = " {0}{1} {2}".format(profix, value, params)
        for key, value in kwargs.items():
            params = " {0}{1}={2} {3}".format(profix, key, value, params)
        if sub_command:
            exec_str = "{0} {1} {2}".format(exec_bin, sub_command, params)
        else:
            exec_str = "{0} {1} ".format(exec_bin, params)
        return exec_str

    @staticmethod
    def make_ssl_files():
        etcd_path = os.path.join(OPENSSL_TMP_DIR, 'etcd')
        if not Achieve.check_achieve(achieve=etcd_path):
            try:
                os.makedirs(etcd_path, 644)
                RecodeLog.info(msg="生成临时文件夹成功:{0}".format(etcd_path))
            except Exception as error:
                RecodeLog.error(msg="生成临时文件夹失败:{0},原因:{1}".format(etcd_path, error))
                assert False
        openssl_params = [
            '/etc/openssl',
            '/etc/openssl/ssl'
        ]
        command_achieve = os.path.join(CMD_FILE_DIR, 'openssl.cmd')
        if not LocalExec.cmd_with_files(
                achieve_object=Achieve,
                achieve=command_achieve,
                params=openssl_params
        ):
            assert False
        openssl_success_lock = os.path.join(OPENSSL_TMP_DIR, "openssl_make_success.lock")
        if not Achieve.touch_achieve(achieve=openssl_success_lock):
            RecodeLog.error(msg="产生lock文件失败：{0}".format(openssl_success_lock))
            assert False
        content = str(time.time())
        Achieve.write_file(achieve=openssl_success_lock, content=content)

    def run_openssl(self):
        RecodeLog.info("=============开始执行openssl部分===============")
        # a = AchieveControl()
        check_file = os.path.join(CURRENT_PATH, 'tmp', 'openssl.success')
        if os.path.exists(check_file):
            RecodeLog.info("=============已存在完成状态文件，跳过执行openssl部分===============")
            return True
        self.write_openssl_config()
        self.make_ssl_files()
        Achieve.touch_achieve(achieve=check_file)
        RecodeLog.info("=============执行完成openssl部分===============")
        return True


class ConfigParserControl:
    def __init__(self):
        self.cf = ReConfigParser()

    def read_achieve(self, achieve):
        """
        :param achieve:
        :return:
        """
        assert os.path.exists(achieve)
        self.cf.read(filenames=achieve, encoding="utf-8")
        self.cf.sections()

    def write_achieve(self, achieve, sections, data, upper=True):
        """
        :param achieve:
        :param sections:
        :param data:
        :param upper:
        :return:
        """
        if not sections:
            RecodeLog.error(msg="sections import error!")
        if isinstance(data, list):
            RecodeLog.error(msg="import data type error!")
        if int(platform.python_version().strip(".")[0]) < 3:
            if not self.cf.has_section(section=sections):
                self.cf.add_section(section=sections)
            for key, value in data.items():
                try:
                    if upper:
                        self.cf.set(sections, key.upper(), value)
                    else:
                        self.cf.set(sections, key, value)
                except Exception as error:
                    RecodeLog.error(
                        msg="数据异常：sections:{0},option:{1},value:{2},原因:{3}".format(
                            sections, key, value, error
                        ))
                    return False
            try:
                with open(name=achieve, mode='ab') as fp:
                    self.cf.write(fp)
                    return True
            except Exception as error:
                RecodeLog.error(
                    msg="写入数据异常：文件名称:{0}原因:{1}".format(
                        achieve, error
                    ))
                return False
        else:
            self.cf[sections] = data
            try:
                with open(achieve, "a") as config_file:
                    self.cf.write(config_file)
                return True
            except Exception as error:
                RecodeLog.error(msg="配置文件写入异常:{0},{1}".format(achieve, error))
                return False


Cf = ConfigParserControl()

__all__ = ['Cf']
