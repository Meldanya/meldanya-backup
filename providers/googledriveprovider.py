import httplib2
import datetime
import operator
import logging
import io

import provider
from apiclient.discovery import build
from apiclient.http import MediaIoBaseUpload
from apiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow, Credentials


class GoogleDriveProvider(provider.Provider):
    oauth_scope = 'https://www.googleapis.com/auth/drive'
    redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    def __init__(self, file_path, config):
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']

        super(GoogleDriveProvider, self).__init__(file_path)

        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
        logging.info('Authorized for Google Drive')

    def read_access_token(self):
        with open(self.currdir + '/.token.google', 'r') as token_file:
            self.credentials = Credentials.new_from_json(token_file.readline())

    def new_access_token(self):
        # Run through the OAuth flow and retrieve credentials
        flow = OAuth2WebServerFlow(self.client_id, self.client_secret,
                                   self.oauth_scope, self.redirect_uri)
        authorize_url = flow.step1_get_authorize_url()

        code = super(GoogleDriveProvider, self).get_auth_code(authorize_url)
        self.credentials = flow.step2_exchange(code)

        with open(self.currdir + '/.token.google', 'w+') as token_file:
            token_file.write(self.credentials.to_json())

    def create_root_dir(self):
        body = {
            'title': 'meldanya_backup',
            'parents': [{'id': 'root'}],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        try:
            req = self.drive_service.files().insert(body=body)
            return req.execute()
        except HttpError as err:
            logging.error('Failed to create folder: %s', err)

    def ensure_root_dir_presence(self):
        files = self.drive_service.files().list().execute()
        backup_root = next((d for d in files['items']
                            if d['title'] == 'meldanya_backup'), None)

        if not backup_root:
            backup_root = self.create_root_dir()

        return backup_root

    def mkdir(self):
        backup_root = self.ensure_root_dir_presence()

        datestr = datetime.datetime.now().strftime('%Y-%m-%dT%H%M')
        body = {
            'title': datestr,
            'parents': [{'id': backup_root['id']}],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        try:
            req = self.drive_service.files().insert(body=body)
            return req.execute()
        except HttpError as err:
            logging.error('Failed to create folder: %s', err)

    def upload(self, filename, backupdir):
        body = {'title': filename,
                'parents': [{'id': backupdir['id']}],
                'mimeType': 'application/octet-stream'}

        try:
            with io.FileIO(filename, 'rb') as f:
                media = MediaIoBaseUpload(f, resumable=True,
                                          mimetype='application/octet-stream')
                req = self.drive_service.files().insert(body=body,
                                                        media_body=media)
                res = req.execute()
                logging.info('Uploaded %s (%s bytes)', res['title'],
                             res['fileSize'])
        except HttpError as err:
            logging.error('Failed to backup %s: %s', filename, err)

    def list_files(self):
        backup_root = self.ensure_root_dir_presence()
        req = self.drive_service.children().list(folderId=backup_root['id'])
        files = req.execute()
        sorted_files = []
        for f in files['items']:
            res = self.drive_service.files().get(fileId=f['id']).execute()
            sorted_files.append(res)

        sorted_files = sorted(sorted_files, key=operator.itemgetter('title'))

        return sorted_files

    def delete_file(self, file_item):
        try:
            fileid = file_item['id']
            self.drive_service.files().delete(fileId=fileid).execute()
        except HttpError as err:
            logging.warning('Failed to delete old backup(%s): %s', fileid, err)
