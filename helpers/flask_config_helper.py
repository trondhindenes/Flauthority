import os
import sys
from ConfigParser import SafeConfigParser

#This is just a helper to find the location of config.ini and parse it
class ConfigHelper(object):

    @staticmethod
    def get_config_path():

        here = os.path.dirname(__file__)
        parent = os.path.abspath(os.path.join(here, os.pardir))
        config_file_path = os.path.join(parent, 'config.ini')

        if os.path.isfile(config_file_path):
            pass
        else:
            raise ValueError(str.format("error reading ini file {0}", config_file_path))

        config = SafeConfigParser()
        try:
            config.read(config_file_path)
        except:
            raise ValueError(str.format("error reading ini file {0}", config_file_path))
        return config

    @staticmethod
    def get_config_variable(config, section, setting_name, default_value=None, get_env=True):
        file_setting = None
        try:
            file_setting = config.get(section, setting_name)
        except:
            pass
        if os.getenv(setting_name, None):
            return os.getenv(setting_name)
        else:
            if file_setting:
                return file_setting
            elif default_value:
                return default_value
            else:
                return None