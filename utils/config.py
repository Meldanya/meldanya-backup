'''The config singleton class.'''
# System includes
import sys
import json
import logging


class Config(dict):

    def __init__(self, config_file, defaults):
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
