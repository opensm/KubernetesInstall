# -*- coding: utf-8 -*-
import os
from lib.setting.base import TMP_ROOT_DIR, INSTALL_ROOT, CNI_PACKAGE, CNI_VERSION, ABS_CNI_PACKAGE

# #cni 临时安装目录
TMP_CNI_DIR = os.path.join(TMP_ROOT_DIR, 'cni')
TMP_CNI_BIN_DIR = os.path.join(TMP_CNI_DIR, 'bin')
TMP_CNI_CONFIG_DIR = os.path.join(TMP_CNI_DIR, 'conf')
TMP_CNI_SSL_DIR = os.path.join(TMP_CNI_DIR, 'ssl')

CNI_HOME = os.path.join(INSTALL_ROOT, 'cni')
CNI_CONFIG_DIR = os.path.join(CNI_HOME, 'conf')
CNI_BIN_DIR = os.path.join(CNI_HOME, 'bin')

__all__ = [
    'CNI_BIN_DIR',
    'CNI_PACKAGE',
    'CNI_CONFIG_DIR',
    'CNI_HOME',
    'CNI_VERSION',
    'TMP_CNI_DIR',
    'TMP_CNI_BIN_DIR',
    'TMP_CNI_CONFIG_DIR',
    'TMP_CNI_SSL_DIR',
    'ABS_CNI_PACKAGE'
]
