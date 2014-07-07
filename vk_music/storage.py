import os
from abc import ABCMeta, abstractmethod, abstractproperty
from progressbar import ProgressBar, Percentage
from .consts import SKIPPED, SAVED

os_join = os.path.join


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
        return [f for f in os.listdir(self.dir)]

    def touch(self, file_name, times=None):
        fname = os_join(self.dir, file_name)
        with open(fname, 'a+'):
            os.utime(fname, times)

    def read(self, file_name, size=None, offset=None):
        with open(os_join(self.dir, file_name)) as f:
            if offset is not None:
                f.seek(offset)
            return f.read(size)

    def write(self, file_name, fp, **kwargs):
        with open(os_join(self.dir, file_name), 'wb+') as f:
            f.write(fp.read())

    def exists(self, file_name):
        return os.path.isfile(os_join(self.dir, file_name))

    def remove(self, file_name):
        os.remove(os_join(self.dir, file_name))


chunk_size = 512 * 1024  # By default notify about every 500Kb write


class ProgressStorage(FileSystemStorage):
    def write_simple(self, *args, **kwargs):
        return super(ProgressStorage, self).write(*args, **kwargs)

    def write(self, file_name, remote, **kwargs):
        file_size = int(remote.info()['Content-Length'])

        pbar = ProgressBar(file_size,
                           widgets=[unicode(kwargs.get('number')), '. [', Percentage(), '] ', '%s %s' % ('Downloading', file_name)]).start()

        if self.exists(file_name):
            with open(os_join(self.dir, file_name), 'rb') as old_f:
                old_f.seek(0, os.SEEK_END)
                old_size = old_f.tell()

                if old_size == file_size:
                    pbar.update(file_size)
                    return SKIPPED

        file_path = os_join(self.dir, file_name)
        dl_path = file_path + '.dl'
        dl_file = open(dl_path, 'wb+')

        steps = 1
        while True:
            dl_file.write(remote.read(chunk_size))
            progress = steps * chunk_size
            if progress > file_size:
                progress = file_size
            pbar.update(progress)
            if progress == file_size:
                break
            steps += 1

        dl_file.close()
        os.rename(dl_path, file_path)

        pbar.finish()

        return SAVED