# -*- coding: utf-8 -*-
import os
import stat
import socket
import fcntl
import struct
import paramiko
import platform
import traceback
from lib.Log import RecodeLog

assert "centos" in platform.platform()


class BsCommand:
    def __init__(self):
        if int(platform.python_version().strip(".")[0]) < 3:
            import commands

            self.exec_proc = commands
        else:
            import subprocess

            self.exec_proc = subprocess

    def format_control_params(self, exec_bin, exec_params, sub_control=None):
        """
        :param exec_bin:
        :param exec_params:
        :param sub_control
        :return:
        :执行栗子： /usr/local/kubernetes/bin/kubectl config use-context ${KUBE_USER}@${CLUSTER_NAME} --kubeconfig=/usr/local/kubernetes/conf/${KUBE_CONFIG}
        """
        param_str = self.format_params(params=exec_params)
        if not param_str:
            return False
        if sub_control:
            exec_str = "{0} {2} {1}".format(exec_bin, param_str, sub_control)
        else:
            exec_str = "{0} {1}".format(exec_bin, param_str)
        return exec_str

    @staticmethod
    def format_params(params):
        """
        :param params:
        :return:
        """
        if not isinstance(params, dict):
            return False
        param = ""
        for key, value in params.items():
            param = "{0} --{1}={2}".format(param, key, value)
        return param

    def cmd_with_files(self, achieve_object, achieve, params):
        """
        :param achieve_object:
        :param achieve:
        :param params:
        :return:
        """
        if not isinstance(params, list):
            RecodeLog.error(msg="传入的参数错误，{0}".format(params))
            return False
        exec_lines = achieve_object.read_exec(exec_file=achieve)

        if not exec_lines:
            return False
        for cmd in exec_lines:
            if cmd.startswith('#'):
                RecodeLog.info(msg=cmd)
                continue
            cmd = cmd.format(*params)
            cmd = cmd.rstrip('\n')
            if not self.cmd(cmd_command=cmd):
                return False
        return True

    def cmd(self, cmd_command, result=False):
        """
        :param cmd_command:
        :param result:
        :return:
        """
        try:
            status, msg = self.exec_proc.getstatusoutput(cmd_command)
            if status != 0:
                raise Exception(msg)
            RecodeLog.info(
                msg="执行成功:{0},返回结果:{1}".format(cmd_command, msg)
            )
            if result:
                return msg
            else:
                return True
        except Exception as error:
            RecodeLog.error(msg="命令:{0},执行失败,原因:{1}".format(cmd_command, error))
            if result:
                return error
            else:
                raise Exception(error)

    @staticmethod
    def get_ip_address(ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
            ret = socket.inet_ntoa(inet[20:24])
            return ret
        except Exception as error:
            RecodeLog.error(msg="获取IP地址失败：{0}".format(error))
            return False

    def check_ip_same(self, address, ifname):
        """
        :param address:
        :param ifname:
        :return:
        """
        local_address = self.get_ip_address(ifname=ifname)
        if not local_address:
            assert False
        if address == local_address:
            return True
        else:
            return False


class SSHFtp(object):

    def __init__(self):

        self.ssh = paramiko.SSHClient()
        self.t = None
        self.host = None
        self.port = None
        self.user = None
        self.passwd = None
        self.pkey = None
        self.timeout = 10
        self.sftp = None

    def setLoginVariable(self, data):
        """
        :param data:
        :return:
        """
        if not isinstance(data, dict):
            raise TypeError("登录输入参数异常，请输入dict类型")
        for key, value in data.items():
            self.__setattr__(key, value)

    def _password_connect(self, **kwargs):

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.ssh._agent:
            pass
        else:
            self.ssh.connect(**kwargs)
            self.t = paramiko.Transport(
                kwargs['hostname'],
                kwargs['port']
            )
        if self.t.is_authenticated():
            pass
        else:
            self.t.connect(username=kwargs['username'], password=kwargs['password'])  # sptf 远程传输的连接
            self.sftp = paramiko.SFTPClient.from_transport(self.t)

    def _key_connect(self, **kwargs):
        # 建立连接
        if os.path.exists(kwargs['pkey']):
            self.pkey = paramiko.RSAKey.from_private_key_file(kwargs['pkey'], )
        # self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(**kwargs)
        self.t.connect(username=kwargs['username'], pkey=kwargs['pkey'])
        self.sftp = paramiko.SFTPClient.from_transport(self.t)

    def connect(self):
        """
        :return:
        """
        if not self.host and not self.port and not self.user:
            raise ValueError("参数列表不完整请检查!")
        if self.passwd and not self.pkey:
            try:
                self._password_connect(
                    username=self.user,
                    password=self.passwd,
                    hostname=self.host,
                    port=self.port,
                    timeout=self.timeout
                )
            except Exception as error:
                RecodeLog.error('ssh password connect faild,{0}'.format(error))
                assert False
        elif self.pkey and not self.passwd:
            if not os.path.exists(self.pkey):
                raise FileExistsError('Keyfile:{0} not exist'.format(self.pkey))
            try:
                self._key_connect(
                    username=self.user,
                    pkey=self.pkey,
                    hostname=self.host,
                    port=self.port,
                    timeout=self.timeout
                )
            except Exception as error:
                RecodeLog.warning('ssh key connect failed, {0},trying to password connect...'.format(error))
                assert False

    def close(self):
        self.t.close()
        self.ssh.close()
        self.sftp = None

    def execute_cmd(self, cmd):

        stdin, stdout, stderr = self.ssh.exec_command(cmd)

        res, err = stdout.read(), stderr.read()
        result = res if res else err

        return result.decode()

    # 从远程服务器获取文件到本地
    def sftp_get(self, remotefile, localfile):
        self.sftp.get(remotefile, localfile)

    # 从本地上传文件到远程服务器
    def sftp_put(self, localfile, remotefile, create_path=True):
        if not self.sftp:
            raise ValueError('账号未登陆！')
        if create_path:
            remote_dir = os.path.dirname(os.path.abspath(remotefile))
            try:
                self.sftp.stat(path=remote_dir)
                RecodeLog.info("远程目录已经存在{1}:{2}".format(localfile, self.host, remotefile))
            except Exception as error:
                RecodeLog.info("远程目录不存在{1}:{2}，即将创建！{3}".format(localfile, self.host, remotefile, error))
                self.sftp.mkdir(path=remote_dir, mode=644)
        RecodeLog.info(msg="开始传输文件:{0},到{1}:{2}".format(localfile, self.host, remotefile))
        self.sftp.put(localfile, remotefile)
        RecodeLog.info(msg="传输完毕文件:{0},到{1}:{2}".format(localfile, self.host, remotefile))

    # 递归遍历远程服务器指定目录下的所有文件
    def _get_all_files_in_remote_dir(self, sftp, remote_dir):
        all_files = list()
        if remote_dir[-1] == os.sep:
            remote_dir = remote_dir[0:-1]

        files = sftp.listdir_attr(remote_dir)
        for x in files:
            filename = remote_dir + os.sep + x.filename

            if stat.S_ISDIR(x.st_mode) and len(os.listdir(x)) > 0:  # 如果是文件夹的话递归处理
                all_files.extend(self._get_all_files_in_remote_dir(sftp, filename))
            else:
                all_files.append(filename)

        return all_files

    def sftp_get_dir(self, remote_dir, local_dir):
        try:

            all_files = self._get_all_files_in_remote_dir(self.sftp, remote_dir)

            for x in all_files:
                local_filename = x.replace(remote_dir, local_dir)
                local_filepath = os.path.dirname(local_filename)

                if not os.path.exists(local_filepath):
                    os.makedirs(local_filepath)

                self.sftp.get(x, local_filename)
        except Exception as error:
            RecodeLog.error('ssh get dir from master failed.{0}'.format(error))
            RecodeLog.error(traceback.format_exc())

    # 递归遍历本地服务器指定目录下的所有文件
    def _get_all_files_in_local_dir(self, local_dir):
        all_files = list()

        for root, dirs, files in os.walk(local_dir, topdown=True):
            RecodeLog.debug(msg="root={0},dirs={1},files={2}".format(root, dirs, files))
            for x in files:
                filename = os.path.join(root, x)
                all_files.append(filename)
            for x in dirs:
                filename = os.path.join(root, x)
                all_files.append(filename)
            RecodeLog.debug(msg="{0}".format(all_files))
        return all_files

    def sftp_put_dir(self, local_dir, remote_dir):
        try:
            if remote_dir.endswith(os.sep):
                remote_dir = remote_dir[0:-1]

            RecodeLog.info(msg="开始将{0},拷贝到主机{1},目录：{2}".format(
                local_dir, self.host, remote_dir
            ))

            all_files = self._get_all_files_in_local_dir(local_dir)
            RecodeLog.debug(msg="本地目录：{0}".format(all_files))
            for x in all_files:
                if os.path.isdir(x):
                    remote_path = x.replace(local_dir, remote_dir)
                else:
                    remote_path = os.path.dirname(x.replace(local_dir, remote_dir))
                RecodeLog.debug(msg="remote_path={0}".format(remote_path))
                try:
                    self.sftp.stat(remote_path)
                except Exception as error:
                    # os.popen('mkdir -p %s' % remote_path)
                    RecodeLog.debug(msg="远程不存在该目录，即将创建:{1},{0}".format(error, remote_path))
                    self.execute_cmd('mkdir -p %s' % remote_path)  # 使用这个远程执行命令
                    RecodeLog.debug(msg="远程不存在该目录，创建成功:{0}".format(remote_path))
                if not os.path.isdir(x):
                    self.sftp.put(x, x.replace(local_dir, remote_dir))
                    RecodeLog.debug(msg="完成将{0},拷贝到主机{1},目录：{2}".format(x, self.host, x.replace(local_dir, remote_dir)))
        except Exception as error:
            RecodeLog.error('ssh get dir from master failed,{0}'.format(error))

    def remote_cmd(self, command):
        """
        :param command:
        :return:
        """
        stdin, stdout, stderr = self.ssh.exec_command(command=command)
        if stdout.channel.recv_exit_status() != 0:
            RecodeLog.error(msg="host:{0},命令:{1}远程执行，请查看具体原因：{2}".format(
                self.host,
                command,
                stderr.read().decode()
            ))
            self.close()
            raise Exception(stderr.read().decode())
        RecodeLog.info(msg="主机:{0},执行成功:{1}".format(self.host, command))


LocalExec = BsCommand()
__all__ = ['SSHFtp', 'LocalExec']
