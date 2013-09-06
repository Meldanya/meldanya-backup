#!/usr/bin/env python
import os
import logging
import argparse
import subprocess

from utils.config import Config
from providers.dropboxprovider import DropboxProvider
from providers.googledriveprovider import GoogleDriveProvider


class Backup(object):

    def __init__(self, abs_path, conf):
        self.abs_path = abs_path
        self.providers = set()
        self.conf = conf

    def backup(self, files, provider):
        self.providers.add(provider)
        root_dir = provider.mkdir()

        for file in files:
            filename = file
            if not self.is_likely_compressed(file):
                filename = self.tar(file)
            orig_filename = filename
            filename = self.encrypt(filename)
            provider.upload(filename, root_dir)
            try:
                os.remove(filename)
                os.remove(orig_filename)
            except IOError:
                logging.warning('Failed to remove %s after backup.', filename)

    def is_likely_compressed(self, file):
        return '.gz' in file or '.tgz' in file

    def tar(self, src):
        name = src + '.tgz'
        cmd = ['tar', 'cfz', name, src]

        ret = subprocess.call(cmd)
        if ret:
            logging.error('Failed to tar: ' + src)

        return name

    def encrypt(self, filename):
        if 'encrypt_pass' not in self.conf:
            return filename
        enc_pass = self.conf['encrypt_pass']

        cmd = ['openssl', 'aes-256-cbc', '-pass', 'file:' + enc_pass,
               '-in', filename, '-out', filename + '.enc']
        ret = subprocess.call(cmd)
        if ret:
            logging.error('Failed to encrypt: ' + filename)
            return filename
        else:
            return filename + '.enc'

    def cleanup(self, keep_files=5):
        for provider in self.providers:
            provider.cleanup(keep_files)


def get_parser():
    parser = argparse.ArgumentParser(description='backup script')
    parser.add_argument('--loglevel', help='set the log level (NONE, DEBUG, '
                        'INFO, WARNING or ERROR) (default: ERROR)',
                        default='ERROR')
    parser.add_argument('--logfile', help='set the log file (absolute path) '
                        '(default: ~/.meldanya_backup.log)',
                        default='~/.meldanya_backup.log')
    parser.add_argument('--config', help='set the config file (absolute path) '
                        '(default: ~/.meldanya_backup.conf)',
                        default='~/.meldanya_backup.conf')

    return parser

# Get the absolute path were executing in
abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'


def main():
    parser = get_parser()
    args = vars(parser.parse_args())

    # Set log level and log file
    if args['loglevel'] == 'NONE':
        logging.disable('ERROR')
        args['loglevel'] = 'WARNING'
    loglevel = args['loglevel'].upper()
    logging.basicConfig(filename=os.path.expanduser(args['logfile']),
                        level=loglevel)

    config = Config(args['config'], {})

    backup = Backup(abs_path, config)
    dropbox = DropboxProvider(abs_path, config['providers']['dropbox'])
    googledrive = GoogleDriveProvider(abs_path, config['providers']['google'])

    logging.info('Backing up to Dropbox...')
    backup.backup(config['providers']['dropbox']['files'], dropbox)

    logging.info('Backing up to Google Drive...')
    backup.backup(config['providers']['google']['files'], googledrive)

    backup.cleanup()

if __name__ == '__main__':
    main()
