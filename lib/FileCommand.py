# -*- coding: utf-8 -*-
import os
import yaml
import platform
import re
import tarfile
from lib.Log import RecodeLog

assert "centos" in platform.platform()


class AchieveControl(object):
    @staticmethod
    def check_dirs(dir_list, create=False):
        """
        :param dir_list:
        :param create:
        :return:
        """
        if not isinstance(dir_list, list):
            raise TypeError("输入的类型错误！")
        for x in dir_list:
            if os.path.exists(x):
                continue
            if create:
                os.makedirs(x)
                RecodeLog.info(msg='创建目录成功: {0}'.format(x))
            else:
                raise FileNotFoundError("目录不存在,{0}!".format(x))

    @staticmethod
    def check_achieve(achieve):
        """
        :param achieve:
        :return:
        """
        return os.path.exists(achieve)

    def touch_achieve(self, achieve):
        """"
        :param achieve:
        :return:
        """
        if not self.check_absolutely_achieve(achieve=achieve):
            RecodeLog.error(
                msg="请检查，文件必须是绝对路径：{0}".format(achieve)
            )
            return False
        try:
            with open(achieve, 'w+') as f:
                f.close()
                RecodeLog.info(
                    msg="执行成功, 产生文件成功：{0}".format(achieve)
                )
                return True
        except Exception as error:
            RecodeLog.error(
                msg="执行成功, 产生文件失败：{0},原因：{1}".format(achieve, error)
            )
            return False

    def write_yaml(self, yaml_name, content):
        """
        :param yaml_name:
        :param content:
        :return:
        """
        if not self.check_achieve(achieve=yaml_name):
            assert self.touch_achieve(achieve=yaml_name)
        assert isinstance(content, dict)
        if not self.check_absolutely_achieve(achieve=yaml_name):
            RecodeLog.error(
                msg="请检查，文件必须是绝对路径：{0}".format(yaml_name)
            )
            return False

        try:
            with open(yaml_name, "w") as f:
                y = yaml.dump(content, f)
                f.close()
                RecodeLog.info(
                    msg="执行成功, 保存内容是：{0}".format(content)
                )
                return True
        except Exception as error:
            RecodeLog.error(
                msg="执行失败, 保存内容是：{0}，原因:{1}".format(content, error)
            )
            return False

    def read_yaml(self, yaml_name):
        """
        :param yaml_name:
        :return:
        """
        if not self.check_absolutely_achieve(achieve=yaml_name):
            RecodeLog.error(
                msg="请检查，文件必须是绝对路径：{0}".format(yaml_name)
            )
            return False
        try:
            with open(yaml_name, "r") as fff:
                y = yaml.load_all(fff.read(), Loader=yaml.FullLoader)
                RecodeLog.info(
                    msg="执行成功, 保存内容是：{0}".format(y)
                )
                return y
        except Exception as error:
            RecodeLog.error(
                msg="读取yaml失败, 原因:{0}".format(error)
            )
            return False

    def check_hosts(self, ipaddr, domain, hosts="/etc/hosts"):
        """
        :param ipaddr:
        :param domain:
        :param hosts:
        :return:
        """
        check_result = self.read_hosts(hosts=hosts)
        if not check_result:
            return False
        if ipaddr not in check_result:
            return False
        if domain not in check_result[ipaddr]:
            return False
        else:
            return True

    @staticmethod
    def check_absolutely_achieve(achieve):
        """
        :param achieve:
        :return:
        """
        if not isinstance(achieve, str):
            return False
        if achieve.startswith(os.sep):
            return True
        else:
            return False

    def read_exec(self, exec_file):
        """
        :param exec_file:
        :return:
        """
        if not self.check_achieve(achieve=exec_file):
            RecodeLog.error(msg="需要执行的文件不存在:{0}".format(exec_file))
            return False
        try:
            with open(exec_file, 'r') as exec_f:
                return exec_f.readlines()
        except Exception as error:
            RecodeLog.error(msg="读取:{0},内容失败,原因:{1}".format(exec_file, error))
            return False

    @staticmethod
    def read_hosts(hosts="/etc/hosts"):
        """
        :param hosts:
        :return:
        """
        host_dict = dict()
        try:
            with open(hosts, 'r') as f:
                data = f.readlines()
                for sub_line in data:
                    sub_line = sub_line.rstrip(" ").lstrip(" ")
                    ipaddress = sub_line.split(" ")[0]
                    domain_list_tmp = sub_line.split(" ")[1:]
                    domain_list = [x for x in domain_list_tmp if x != ""]
                    host_dict.setdefault(ipaddress, []).extend(domain_list)
            RecodeLog.info(
                msg="执行成功, 返回的内容：{0}".format(host_dict)
            )
            return host_dict
        except Exception as error:
            RecodeLog.error(
                msg="保存文件:{0}失败, 数据:{2},原因:{1}".format(hosts, error, host_dict)
            )
            return False

    def write_file(self, achieve, content, mode="a"):
        """
        :param achieve:
        :param content:
        :param mode:
        :return:
        """
        if not self.check_achieve(achieve=achieve):
            # 不能创建文件直接退出
            assert self.touch_achieve(achieve=achieve)
        try:
            with open(achieve, mode=mode) as f:
                f.write(content)
                RecodeLog.info(
                    msg="写入:{0}成功, 返回的内容：{1}".format(achieve, content)
                )
                return True
        except IOError as error:
            RecodeLog.error(
                msg="写入文件:{0},失败, 原因：{1}".format(achieve, error)
            )
            return False

    def write_hosts(self, ipaddr, domain, hosts="/etc/hosts"):
        """
        :param ipaddr:IP地址
        :param domain:解析域名或者host
        :param hosts:修改的文件
        :return:
        """
        if self.check_hosts(ipaddr=ipaddr, domain=domain, hosts=hosts):
            return True
        domain_line = "{0} {1}\n".format(ipaddr, domain)
        if not self.write_file(achieve=hosts, content=domain_line):
            return False
        else:
            return True

    def alter_achieve(self, achieve, old_str, new_str, matching=None):
        """
        替换文件中的字符串
        :param achieve:文件名
        :param old_str:旧字符串
        :param new_str:新字符串
        :param matching: 需要替换的匹配行，不指定则为不匹配全部替换
        :return:
        """
        if not self.check_achieve(achieve=achieve):
            return False
        if int(platform.python_version().strip(".")[0]) < 3:
            achieve_params = {
                'name': achieve,
                'mode': "r"
            }
        else:
            achieve_params = {
                'file': achieve,
                'mode': "r",
                "encoding": "utf-8"
            }
        with open(**achieve_params) as f1:
            data = f1.readlines()
            for i in range(0, len(data)):
                if matching:
                    if not re.search(matching, data[i]):
                        continue
                    RecodeLog.info(msg="匹配到:{0},开始替换：{1}=>{2}".format(
                        matching,
                        new_str,
                        data[i]
                    ))
                    data[i] = re.sub(old_str, new_str, data[i])
                else:
                    data[i] = re.sub(old_str, new_str, data[i])
        achieve_params['mode'] = 'w'
        with open(**achieve_params) as f2:
            f2.writelines(data)
        return True

    @staticmethod
    def tar_decompression(achieve, target_path):
        """
        :param achieve:
        :param target_path:
        :return:
        """
        if not isinstance(achieve, str):
            RecodeLog.error(msg="输入参数不正确！")
            return False
        if not achieve.endswith("tar.gz") and not achieve.endswith('.tgz'):
            RecodeLog.error(msg="文件类型或者扩展名不正确:{0}".format(achieve))
            return False

        try:
            tar = tarfile.open(achieve, "r:gz")
            file_names = tar.getnames()
            for file_name in file_names:
                tar.extract(file_name, target_path)
            tar.close()
            RecodeLog.info(msg="解压文件成功：{0},到：{1}".format(achieve, target_path))
            return True
        except Exception as error:
            RecodeLog.error(msg="解压文件异常：{0},Error:{1}".format(achieve, error))
            return False


Achieve = AchieveControl()

__all__ = ['Achieve']
