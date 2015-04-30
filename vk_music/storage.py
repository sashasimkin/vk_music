import os
import sys
from abc import ABCMeta, abstractmethod

from .consts import SKIPPED, SAVED


class BaseStorage(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def get_id(self):
        """
        Storage object identification
        """

    @abstractmethod
    def touch(self, file_name):
        """
        Touch file name
        """

    @abstractmethod
    def read(self, file_name, size=None, offset=None):
        """
        Read bytes from file
        """

    @abstractmethod
    def write(self, file_name, fp, **kwargs):
        """
        Write data
        """

    @abstractmethod
    def exists(self, file_name):
        """
        Is file with that name exists?
        """

    @abstractmethod
    def remove(self, file_name):
        """
        Remove file with this name
        """


class FileSystemStorage(BaseStorage):
    def __init__(self, directory):
        self.dir = directory

    def get_id(self):
        return self.dir

    def files_list(self):
        for name in os.listdir(self.dir):
            try:
                name = name.decode(sys.getfilesystemencoding())
            except UnicodeEncodeError:  # Assume that it's already unicode
                pass
            yield name

    def touch(self, file_name, times=None):
        fname = os.path.join(self.dir, file_name)
        with open(fname, 'a+'):
            os.utime(fname, times)

    def read(self, file_name, size=None, offset=None):
        with open(os.path.join(self.dir, file_name)) as f:
            if offset is not None:
                f.seek(offset)
            return f.read(size)

    def write_simple(self, file_name, fp):
        with open(os.path.join(self.dir, file_name), 'wb+') as f:
            f.write(fp.read())

    def write(self, file_name, fp, **kwargs):
        if self.exists(file_name):
            return SKIPPED

        self.write_simple(file_name, fp)

        return SAVED

    def exists(self, file_name):
        return os.path.isfile(os.path.join(self.dir, file_name))

    def remove(self, file_name):
        os.remove(os.path.join(self.dir, file_name))


class CachedStorageMixin(object):
    def files_list(self):
        if not hasattr(self, '_files_list'):
            # Load immediately into memory. We don't need generator here
            self._files_list = list(super(CachedStorageMixin, self).files_list())

        return self._files_list

    def exists(self, file_name):
        return file_name in self.files_list()