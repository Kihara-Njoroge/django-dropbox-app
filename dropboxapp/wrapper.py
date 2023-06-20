from dropbox.files import FolderMetadata
from dropbox.oauth import DropboxOAuth2Flow

from .dropbox import DropBoxStorage

# ----------------------------------------------------------------------------
def human_readable(size):
    '''
    Create a human readable representation of a quantity in bytes. 

    The numerical quantity is expressed by a three-digits float, followed by
    a suffix (e.g., 12345 -> '12.0 KB').
    '''
    if size < 1024:
        return size
    seq = ['', ' KB', ' MB', ' GB', ' TB']
    exp = 0
    while size > 1023:
        size = size / 1024.0
        exp += 1
    label = f"{size:.3f}"[:4]
    if label[-1] == '.':
        label = label[:-1]
    return label + seq[exp]


# ----------------------------------------------------------------------------
class DropboxMetaFile:
    '''This class contains some information about a Dropbox file.

    Attributes:
    path   : the file's absolute path in Dropbox
    url    : same as path, but without the initial '/'
    name   : the file's name
    is_dir : whether the file is a directory
    date   : the server's date when the file was last modified
    size   : the file's size as a human readable string
    '''

    # ........................................................................
    def __init__(self, metadata):
        self.path = metadata.path_display
        self.url = self.path[1:]
        self.name = metadata.name
        if isinstance(metadata, FolderMetadata):
            self.is_dir = True
        else:
            self.is_dir = False
            self.date = metadata.server_modified
            self.size = human_readable(metadata.size)


# ----------------------------------------------------------------------------
class DropboxWrapper():
    '''This class offer simple access to Dropbox API.

    It uses Monthe's custom Storage class to access Dropbox files, but also
    explores other methods from Dropbox API.
    '''

    # ........................................................................
    def __init__(self, app_key):
        self.app_key = app_key

    # ........................................................................
    def request_access(self, session, redirect):
        '''Start authorization request to access a Dropbox account.
        
        Return a URL that must be accessed by the user in order to grant
        authorization to his Dropbox account.

        Parameters:
        session  : dict containing the current session information
        redirect : URL that will be redirected after authorization is granted;
                   validation data will be passed by GET
        '''
        self.auth = DropboxOAuth2Flow(
                self.app_key,
                redirect,
                session,
                "dropbox-auth-csrf-token",
                use_pkce=True,
                token_access_type='online')
        return self.auth.start()

    # ........................................................................
    def conclude_access(self, query):
        '''Conclude authorization process, granting access to Dropbox.

        Return True if the access was granted.
        
        Parameter:
        query : dict containing the GET information sent to a redirected URL
        '''
        try:
            result = self.auth.finish(query)
            self.storage = DropBoxStorage(
                    oauth2_access_token=result.access_token)
            return self.has_access()
        except Exception as e:
            print(e)
            return False

    # ........................................................................
    def has_access(self):
        '''Whether there is access to a Dropbox account or not.'''
        try:
            self.storage.client.users_get_current_account() 
            return True
        except Exception:
            return False

    # ........................................................................
    def listdir(self, path):
        '''List all files and directories in the given path.
        
        It is similar to Storage.listdir(), but instead of returning two
        lists of names (one for folders and another for files), it returns
        a single list of DropboxMetaFile. The list is sorted in alphabetical
        order, and folders are places first. This method is faster than 
        calling the API many times to obtain metadata for each file retrieved.

        Parameter:
        path : a Dropbox absolute path
        '''
        result = self.storage.client.files_list_folder(path)
        files = list()
        for metadata in result.entries:
            files.append(DropboxMetaFile(metadata))
        files.sort(key=lambda fi: fi.name.lower())
        files.sort(key=lambda fi: -1 if fi.is_dir else 1)
        return files

    # ........................................................................
    def get_file(self, name):
        '''Obtain a File object after its name.'''
        return self.storage.open(name)

    # ........................................................................
    def upload_file(self, path, upfile):
        '''Upload a File object to Dropbox.

        Parameters:
        path   : the folder's absolute path where the file will be stored
        upfile : the File object to be uploaded; its name is added to path 
                 in order to create its final name on Dropbox
        '''
        name = ('/' if path == '' else ('/' + path + '/')) + upfile.name
        self.storage.save(name, upfile)
        return name

    # ........................................................................
    def create_folder(self, path, name):
        '''Create a folder in Dropbox.

        If the new folder's name contains '/', it will create a hierarchy of
        subfolders.

        Parameters:
        path : the folder's absolute path where the new folder will be created
        name : the new folder's name
        '''
        name = ('/' if path == '' else ('/' + path + '/')) + name
        self.storage.client.files_create_folder(name)

