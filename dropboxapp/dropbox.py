from io import BytesIO
from shutil import copyfileobj
from tempfile import SpooledTemporaryFile
import os
from django.core.exceptions import SuspiciousFileOperation

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils._os import safe_join
from django.utils.deconstruct import deconstructible
from decouple import config
from dropbox import Dropbox
from dropbox.exceptions import ApiError
from dropbox.files import (
    CommitInfo, FolderMetadata, UploadSessionCursor, WriteMode,
)

_DEFAULT_TIMEOUT = 100
_DEFAULT_MODE = 'add'


def get_available_overwrite_name(name, max_length):
    if max_length is None or len(name) <= max_length:
        return name

    dir_name, file_name = os.path.split(name)
    file_root, file_ext = os.path.splitext(file_name)
    truncation = len(name) - max_length

    file_root = file_root[:-truncation]
    if not file_root:
        raise SuspiciousFileOperation(
            'Storage tried to truncate away entire filename "%s". '
            'Please make sure that the corresponding file field '
            'allows sufficient "max_length".' % name
        )
    return os.path.join(dir_name, "{}{}".format(file_root, file_ext))


def setting(name, default=None):
    return getattr(settings, name, default)


class DropBoxStorageException(Exception):
    pass


class DropBoxFile(File):
    def __init__(self, name, storage):
        self.name = name
        self._storage = storage
        self._file = None

    def _get_file(self):
        if self._file is None:
            self._file = SpooledTemporaryFile()
            file_metadata, response = \
                self._storage.client.files_download(self.name)
            if response.status_code == 200:
                with BytesIO(response.content) as file_content:
                    copyfileobj(file_content, self._file)
            else:
                raise DropBoxStorageException(
                    "Dropbox server returned a {} response when accessing {}"
                    .format(response.status_code, self.name)
                )
            self._file.seek(0)
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)


@deconstructible
class DropBoxStorage(Storage):
    location = setting('DROPBOX_ROOT_PATH', '/')
    oauth2_access_token = config('DROPBOX_OAUTH2_TOKEN')
    timeout = config('DROPBOX_TIMEOUT', _DEFAULT_TIMEOUT)
    write_mode = config('DROPBOX_WRITE_MODE', _DEFAULT_MODE)

    CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self, oauth2_access_token=oauth2_access_token, root_path=location, timeout=timeout,
                 write_mode=write_mode):
        if oauth2_access_token is None:
            raise ImproperlyConfigured("You must configure an auth token.")

        self.root_path = root_path
        self.write_mode = write_mode
        self.client = Dropbox(oauth2_access_token, timeout=timeout)

    def _full_path(self, name):
        if name == '/':
            name = ''
        return safe_join(self.root_path, name).replace('\\', '/')

    def delete(self, name):
        self.client.files_delete(self._full_path(name))

    def exists(self, name):
        try:
            return bool(self.client.files_get_metadata(self._full_path(name)))
        except ApiError:
            return False

    def listdir(self, path):
        directories, files = [], []
        full_path = self._full_path(path)

        if full_path == '/':
            full_path = ''

        metadata = self.client.files_list_folder(full_path)
        for entry in metadata.entries:
            if isinstance(entry, FolderMetadata):
                directories.append(entry.name)
            else:
                files.append(entry.name)
        return directories, files

    def size(self, name):
        metadata = self.client.files_get_metadata(self._full_path(name))
        return metadata.size

    def modified_time(self, name):
        metadata = self.client.files_get_metadata(self._full_path(name))
        return metadata.server_modified

    def accessed_time(self, name):
        metadata = self.client.files_get_metadata(self._full_path(name))
        return metadata.client_modified

    def url(self, name):
        media = self.client.files_get_temporary_link(self._full_path(name))
        return media.link

    def _open(self, name, mode='rb'):
        remote_file = DropBoxFile(self._full_path(name), self)
        return remote_file

    def _save(self, name, content):
        content.open()
        if content.size <= self.CHUNK_SIZE:
            self.client.files_upload(content.read(), self._full_path(
                name), mode=WriteMode(self.write_mode))
        else:
            self._chunked_upload(content, self._full_path(name))
        content.close()
        return name

    def _chunked_upload(self, content, dest_path):
        upload_session = self.client.files_upload_session_start(
            content.read(self.CHUNK_SIZE)
        )
        cursor = UploadSessionCursor(
            session_id=upload_session.session_id,
            offset=content.tell()
        )
        commit = CommitInfo(path=dest_path, mode=WriteMode(self.write_mode))

        while content.tell() < content.size:
            if (content.size - content.tell()) <= self.CHUNK_SIZE:
                self.client.files_upload_session_finish(
                    content.read(self.CHUNK_SIZE), cursor, commit
                )
            else:
                self.client.files_upload_session_append_v2(
                    content.read(self.CHUNK_SIZE), cursor
                )
                cursor.offset = content.tell()

    def get_available_name(self, name, max_length=None):
        name = self._full_path(name)
        if self.write_mode == 'overwrite':
            return get_available_overwrite_name(name, max_length)
        return super().get_available_name(name, max_length)
