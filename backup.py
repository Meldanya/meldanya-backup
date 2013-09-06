#!/usr/bin/env python
import os
import logging
import argparse
import subprocess

from utils.config import Config
from providers.dropboxprovider import DropboxProvider
from providers.googledriveprovider import GoogleDriveProvider


class Backup(object):
    """The main class that performs compressing, encrypting and backing up to
    a given provider (e.g. Google Drive or Dropbox). The main work is done by
    the backup() method.

    :param abs_path: the path to the script.
    :param conf: the configuration dictionary.
    """

    def __init__(self, abs_path, conf):
        self.abs_path = abs_path
        self.providers = set()
        self.conf = conf

    def backup(self, files, provider):
        """Performs the main work of tar'ing, encrypting and uploading all
        files in the provided list. It will use the provider specified by the
        provider parameter.

        :param files: the list of files of folders to backup.
        :param provider: the backend storage provider to use (e.g. Google Drive
                         or Dropbox) which must extend the providers.Provider
                         class (see that class for details on the methods that
                         must be implemented).
        """
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

    def is_likely_compressed(self, filename):
        """Helper method that tries to guess if a file is already compressed.

        :param filename: the filename to check.

        :return bool. `True` if the file is likely compressed, `False`
                      otherwise.
        """
        return '.gz' in filename or '.tgz' in filename

    def tar(self, src):
        """Archives and compresses the folder given in the src parameter.

        :param src: the folder to archive and compress.

        :return string. the new filename of the compressed file.
        """
        name = src + '.tgz'
        cmd = ['tar', 'cfz', name, src]

        ret = subprocess.call(cmd)
        if ret:
            logging.error('Failed to tar: ' + src)

        return name

    def encrypt(self, filename):
        """Encrypts the file provided in the filename parameter. It currently
        calls `openssl` to encrypt it with aes-256-cbc. Plans exist to
        implement it in Python instead.

        :param filename: the filename to encrypt.

        :return string. the new filename of the encrypted file or the original
                        filename if no password file was specified in the
                        config file.
        """
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
        """Cleans up old backups for all providers that has been used by this
        backup instance.

        :param keep_files: the number of backups to keep.
        """
        for provider in self.providers:
            provider.cleanup(keep_files)

# Get the absolute path were executing in
abs_path = os.path.dirname(os.path.realpath(__file__)) + '/'

def get_parser():
    """Creates a parser for the command line options.

    :return parser. the argument parser to use to parse the command line
                    arguments.
    """
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

def absify(path):
    """Simple helper to make a path absolute, either from expanding ~ or from
    prepending the absolute path of this script.

    :param path: the path to make absolute

    :return string. the path absified.
    """
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = abs_path + path

    return path


def main():
    parser = get_parser()
    args = vars(parser.parse_args())

    # Set log level and log file
    if args['loglevel'] == 'NONE':
        logging.disable('ERROR')
        args['loglevel'] = 'WARNING'
    loglevel = args['loglevel'].upper()
    args['logfile'] = absify(args['logfile'])
    logging.basicConfig(filename=args['logfile'], level=loglevel)

    args['config'] = absify(args['config'])
    config = Config(args['config'])

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
