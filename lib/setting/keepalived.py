# -*- coding: utf-8 -*-
import os
from lib.settings import INSTALL_ROOT
from lib.setting.base import TMP_PACKAGE_PATH

KEEPALIVED_PACKAGE = "keepalived-2.0.13"

KEEPALIVED_HOME = os.path.join(INSTALL_ROOT, 'keepalived')

ABS_KEEPALIVED_PACKAGE = os.path.join(TMP_PACKAGE_PATH, "{0}.tar.gz".format(KEEPALIVED_PACKAGE))

__all__ = [
    'KEEPALIVED_HOME',
    'KEEPALIVED_PACKAGE',
    'ABS_KEEPALIVED_PACKAGE',
]
