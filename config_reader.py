import configparser
import os 

# config read
config = configparser.ConfigParser(allow_no_value=True)
config_file = "config.ini"
if not os.path.isfile(config_file):
    config_file = "config.ini-dist"
config.read(config_file)

def get(section, name, fallback=None):
    return config.get(section, name, fallback=fallback)