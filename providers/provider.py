import os
import logging


class Provider(object):

    def __init__(self, file_path):
        self.file_path = file_path
        self.currdir = os.path.dirname(__file__)

        try:
            self.read_access_token()
        except IOError:
            logging.warning("Failed to acquire credentials from file")
            self.new_access_token()

    def read_access_token(self):
        raise

    def new_access_token(self):
        raise

    def get_auth_code(self, authorize_url):
        print 'You know the drill: ' + authorize_url
        return raw_input('Enter authorization code: ').strip()

    def upload(self, filename):
        raise

    def list_files(self):
        raise

    def delete_file(self, file_item):
        raise

    def cleanup(self, keep_files=5):
        filelist = self.list_files()

        num_to_clean = len(filelist) - keep_files
        if num_to_clean > 0:
            for i in range(0, num_to_clean):
                self.delete_file(filelist[i])
            logging.info('Cleaned %d files',  num_to_clean)
        else:
            logging.info('Nothing to clean')
