import platform

class ConfigOperate(object):
    def get_distribution_info():
        print("called.")
        return platform.linux_distribution()

class SystemConfig(object):
    linux_dist_info = ConfigOperate.get_distribution_info()
