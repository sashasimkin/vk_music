import sys
import os
import math
from functools import partial

from six.moves import urllib
from progressbar import ProgressBar, Percentage

from .storage import FileSystemStorage, CachedStorageMixin
from .consts import SKIPPED, SAVED
from .vk_music import Song


class ProgressStorage(FileSystemStorage):
    """
    Right not unusable because of multi-threading
    But can be used within one thread
    """

    def __init__(self, directory, chunk_size=512 * 1024):  # By default notify about every 500Kb write
        self.chunk_size = chunk_size
        super(ProgressStorage, self).__init__(directory)

    def write(self, file_name, remote, **kwargs):
        """
        Write remote to filesystem using given name

        :param file_name:
        :param remote:
        :param progress_hook: function accepting same arguments as urlretrieve's reporthook
        :param kwargs:
        :return:
        """
        chunk_size = self.chunk_size
        file_size = int(remote.info()['Content-Length'])

        progress_hook = kwargs.get('progress_hook')
        if not progress_hook:
            raise TypeError('Write in {} should be called with progress_hook'.format(self.__class__.__name__))

        if self.exists(file_name):
            if file_size == os.path.getsize(os.path.join(self.dir, file_name)):
                progress_hook(int(math.ceil(file_size / chunk_size)), chunk_size, file_size)
                return SKIPPED

        file_path = os.path.join(self.dir, file_name)
        dl_path = file_path + '.dl'
        dl_file = open(dl_path, 'wb+')

        buf = ''
        blocknum = 1
        try:
            while True:
                chunk = remote.read(chunk_size)
                buf += chunk
                progress_hook(blocknum, chunk_size, file_size)
                if chunk == "":
                    break
                blocknum += 1

            dl_file.write(buf)
        finally:
            dl_file.close()

        os.rename(dl_path, file_path)

        return SAVED


class SafeFsStorage(CachedStorageMixin, FileSystemStorage):
    """
    The `Safe` meaning is that it checks for corrupted (or just different but with same name) files
    based on server's response
    """

    def write(self, file_name, remote, **kwargs):
        file_size = int(remote.info()['Content-Length'])

        if self.exists(file_name):
            if file_size == os.path.getsize(os.path.join(self.dir, file_name)):
                return SKIPPED

        self.write_simple(file_name, remote)

        return SAVED


def progress_hook(pbar, num, block_size, size):
    progress = num * block_size
    pbar.update(progress)
    if progress >= size:
        pbar.finish()


class SongWithProgress(Song):
    def save(self, **kwargs):
        """
        Save song
        Download from self.url and save to self.path with self.name
        """
        if not hasattr(self, 'url'):
            raise RuntimeError('Can not load song')

        # r means remote file
        r = urllib.request.urlopen(self.url)
        file_size = int(r.info()['Content-Length'])

        # Sometimes it's unicode, sometimes not.
        # But actually it should always be unicode
        # Anyway this line will stay as is just to be sure
        name = self.name.encode(sys.getfilesystemencoding()) if isinstance(self.name, unicode) else self.name

        pbar = ProgressBar(file_size,
                           widgets=[unicode(kwargs.get('number')),
                                    '. [', Percentage(), '] ',
                                    '%s %s' % ('Downloading', name)]).start()

        bound_hook = partial(progress_hook, pbar)
        # Such kind of manipulation need later in case of errors and broken files
        return self.storage.write(self.name, r, progress_hook=bound_hook)