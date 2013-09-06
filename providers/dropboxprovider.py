import logging
import datetime

import provider
import dropbox
import ast
import os


class DropboxProvider(provider.Provider):

    def __init__(self, file_path, config):
        self.app_key = config['app_key']
        self.app_secret = config['app_secret']

        super(DropboxProvider, self).__init__(file_path)

        self.client = dropbox.client.DropboxClient(self.access_token)
        logging.info('Authorized for Dropbox')

    def read_access_token(self):
        with open(self.currdir + '/.token.dropbox', 'r') as token_file:
            file_content = token_file.readline()
            self.access_token, self.user_id = ast.literal_eval(file_content)

    def new_access_token(self):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.app_key,
                                                          self.app_secret)

        authorize_url = flow.start()
        code = super(DropboxProvider, self).get_auth_code(authorize_url)
        self.access_token, self.user_id = flow.finish(code)

        # Cache the result to a file (yep, we're THAT safe!)
        with open(self.currdir + '/.token.dropbox', 'w+') as token_file:
            token_file.write(str((self.access_token, self.user_id)))

    def mkdir(self):
        datestr = datetime.datetime.now().strftime('%Y-%m-%dT%H%M')
        try:
            res = self.client.file_create_folder('/' + datestr)
            return res['path']
        except dropbox.rest.ErrorResponse:
            logging.error('Failed to create backup directory')

        return None

    def upload(self, filename, backupdir):
        ulname = os.path.basename(filename)

        try:
            with open(filename, 'rb') as f:
                res = self.client.put_file(backupdir + '/' + ulname, f)
                logging.info('Uploaded %s(%d bytes)',
                             os.path.basename(res['path']), res['bytes'])
        except dropbox.rest.ErrorResponse as e:
            logging.error('Failed to upload file: %s', e)

    def list_files(self):
        return self.client.metadata('/')['contents']

    def delete_file(self, file_item):
        try:
            self.client.file_delete(file_item['path'])
        except dropbox.rest.ErrorResponse as e:
            logging.error('Failed to delete old backup: %s', e)
