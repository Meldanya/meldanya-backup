import os
import logging


class Provider(object):
    """The base class for all storage providers.

    All providers MUST implement the interface specified here in order for the
    backup script to function properly.
    """

    def __init__(self):
        """Initializes a new Provider object, this constructor MUST be called
        by the subclasses of this class. Before calling this constructor, the
        sub-provider MUST initialize any application/client key/secret.

        The constructor will call the read_access_token() method, which MUST be
        implemented by the subclasses. This method will try to read the file
        with the cached access token and call new_access_token() if that
        failed. That method MUST also be implemented by subclasses and should
        (interactively) acquire a new access token and cache that to a file.
        """
        self.currdir = os.path.dirname(__file__)

        try:
            self.read_access_token()
        except IOError:
            logging.warning("Failed to acquire credentials from file")
            self.new_access_token()

    def read_access_token(self):
        """The method that (in subclasses) should read the cached access token
        from a file. The file name should be ".token.<provider name>" and be
        stored in the self.currdir path (defined in this class).

        The subclass implementation should raise an IOError if the read failed
        (e.g. there was no file to read from, etc.).
        """
        raise

    def new_access_token(self):
        """The method that (in subclasses) should perform an interactive
        authentication of the application (to the user) to allow it access to
        the user's account. The credentials MUST be saved in a class variable
        to allow access to it in the rest of the class.

        The authentication SHOULD be performed via OAuth.

        Once the authentication is done, the credentials should be written to a
        file (which can be read in the read_access_token() method).
        """
        raise

    def get_auth_code(self, authorize_url):
        """Helper method to get the authorization code from the user.

        :param authorize_url: the authorization URL to display to the user.

        :return string. The result the user inputs after authorizing the app.
        """
        print 'You know the drill: ' + authorize_url
        return raw_input('Enter authorization code: ').strip()

    def mkdir(self):
        """A method that MUST be implemented by subclasses to create a new
        directory. The directory's name SHOULD be the current date/time when
        the method is called.

        :return object. An object of the type needed by the subclass in the
                        upload() method to allow it to upload backup items to
                        the created dir.
        """
        raise

    def upload(self, filename, backupdir):
        """The method that MUST be implemented by subclasses to upload a file.
        The implementation details are left fairly free but the function MUST
        log any errors that are encountered (with the logging module).
        """
        raise

    def list_files(self):
        """A method that MUST be implemented by subclasses to get a list of the
        folders in the backup root dir. The list MUST be returned in ascending
        order with regards to the creation date.

        :return list. the list of folders in ascending order of creation date.
        """
        raise

    def delete_file(self, file_item):
        """A method that MUST be implemented by subclasses to delete the given
        file item.

        :param file_item: the file item (with specific type for the different
                          subclasses) that should be deleted. This is one of
                          the items in the list returned by the list_files()
                          method.
        """
        raise

    def cleanup(self, keep_files=5):
        """Performs a cleanup (i.e. removing old backup items) for this
        provider. Will call the list_files() method to get a list of the backup
        items (i.e. folders) and iterate through all but the 5 last items in
        the list and call delete_file() on them.

        :param keep_files: the number of backup items to keep, default is 5.
        """
        filelist = self.list_files()

        num_to_clean = len(filelist) - keep_files
        if num_to_clean > 0:
            for i in range(0, num_to_clean):
                self.delete_file(filelist[i])
            logging.info('Cleaned %d files',  num_to_clean)
        else:
            logging.info('Nothing to clean')
