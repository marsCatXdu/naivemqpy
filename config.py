#!/usr/bin/python3
# -*- coding: utf-8 -*-

import platform

class ConfigOperate(object):

    def get_distribution_info():
        return platform.linux_distribution()

class SystemConfig(object):

    linux_dist_info = ConfigOperate.get_distribution_info()
