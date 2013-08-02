# Copyright (C) 2011 Linaro Limited
#
# Author: Linaro Validation Team <linaro-dev@lists.linaro.org>
#
# This file is part of LAVA Dispatcher.
#
# LAVA Dispatcher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# LAVA Dispatcher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses>.

from unittest import TestCase

import lava_dispatcher.config
from lava_dispatcher.config import get_config, get_device_config
from lava_dispatcher.utils import string_to_list

from lava_dispatcher.tests.helper import *

test_config_dir = os.path.join(os.path.dirname(__file__), 'test-config')


class TestConfigData(TestCase):

    def setUp(self):
        setup_config_dir()
        lava_dispatcher.config.custom_config_path = test_config_dir

    def tearDown(self):
        cleanup_config_dir()
        lava_dispatcher.config.custom_config_path = None

    def test_beagle01_uboot_cmds(self):
        beagle01_config = get_device_config("beaglexm01")
        expected = [
            "mmc init",
            "mmc part 0",
            "setenv bootcmd 'fatload mmc 0:3 0x80000000 uImage; fatload mmc "
            "0:3 0x81600000 uInitrd; bootm 0x80000000 0x81600000'",
            "setenv bootargs ' console=tty0 console=ttyO2,115200n8 "
            "root=LABEL=testrootfs rootwait ro earlyprintk fixrtc "
            "nocompcache vram=12M omapfb.debug=y "
            "omapfb.mode=dvi:1280x720MR-16@60'",
            "boot"]
        uboot_cmds = beagle01_config.boot_cmds
        self.assertEquals(expected, string_to_list(uboot_cmds))

    def test_server_ip(self):
        server_config = get_config()
        expected = "192.168.200.200"
        lava_server_ip = server_config.lava_server_ip
        self.assertEqual(expected, lava_server_ip)
