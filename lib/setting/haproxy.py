# -*- coding: utf-8 -*-
import os
from lib.settings import INSTALL_ROOT
from lib.setting.base import TMP_PACKAGE_PATH

HAPROXY_PACKAGE = "haproxy-1.5.19"
HAPROXY_HOME = os.path.join(INSTALL_ROOT, 'haproxy')
ABS_HAPROXY_PACKAGE = os.path.join(TMP_PACKAGE_PATH, "{0}.tar.gz".format(HAPROXY_PACKAGE))

__all__ = [
    'HAPROXY_PACKAGE',
    'HAPROXY_HOME',
    'ABS_HAPROXY_PACKAGE'
]
