import os
from dropbox.files import FolderMetadata, FileMetadata
from dropbox.oauth import DropboxOAuth2Flow
from django.core.exceptions import SuspiciousFileOperation


from .dropbox import DropBoxStorage

def human_readable(size):
    '''Create a human readable representation of a quantity in bytes. '''
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


class DropboxMetaFile:
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


class DropboxWrapper():
    def __init__(self, app_key):
        self.app_key = app_key

    def request_access(self, session, redirect):
        self.auth = DropboxOAuth2Flow(
                self.app_key,
                redirect,
                session,
                "dropbox-auth-csrf-token",
                use_pkce=True,
                token_access_type='online')
        return self.auth.start()

    def conclude_access(self, query):
        try:
            result = self.auth.finish(query)
            self.storage = DropBoxStorage(
                    oauth2_access_token=result.access_token)
            return self.has_access()
        except Exception as e:
            print(e)
            return False

    def has_access(self):
        try:
            self.storage.client.users_get_current_account() 
            return True
        except Exception:
            return False

    def listdir(self, path):
        '''List all files and directories in the given path.'''
        result = self.storage.client.files_list_folder(path)
        files = list()
        for metadata in result.entries:
            files.append(DropboxMetaFile(metadata))
        files.sort(key=lambda fi: fi.name.lower())
        files.sort(key=lambda fi: -1 if fi.is_dir else 1)
        return files

    def get_file(self, name):
        return self.storage.open(name)

    def upload_file(self, path, upfile):
        name = ('/' if path == '' else ('/' + path + '/')) + upfile.name
        try:
            self.storage.save(name, upfile)
        except SuspiciousFileOperation as e:
            pass
        return name

    def create_folder(self, path, name):
        name = ('/' if path == '' else ('/' + path + '/')) + name
        self.storage.client.files_create_folder(name)

    def delete_file(self, path):
        self.storage.client.files_delete_v2('/' + path)
        


