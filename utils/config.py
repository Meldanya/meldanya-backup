import sys
import json
import logging


class Config(dict):
    """The config class which functions exactly as a dict but reads the content
    of the dict from the config file.

    If the config file can't be opened or parsed, the class will output the
    error and then exit the entire program. We can't really go on without
    configuration (e.g. what should we backup?).

    :param config_file: the config file to read from.
    :param defaults: a dict of default items (optional)"""

    def __init__(self, config_file, defaults=None):
        dict.__init__(self, defaults or {})
        exit = False
        try:
            with open(config_file, 'r') as conf:
                config = json.loads(''.join(conf.readlines()))
                self.update(config)
        except IOError as err:
            logging.error('Failed to read config file: ' + str(err))
            exit = True
        except ValueError as err:
            logging.error('Failed to parse config file: ' + str(err))
            exit = True

        if exit:
            print 'A fatal error occured, see log file for details'
            sys.exit(-1)
