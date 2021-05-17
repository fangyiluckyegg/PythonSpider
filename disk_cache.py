import os                                          # os.path 模块主要用于获取文件的属性
import re
import urllib.parse
import shutil                                      # 高级的文件操作模块，就是对os中文件操作的补充
import zlib                                        # 文件缓存压缩工具          
from datetime import datetime, timedelta           # 日期、时间操作工具
try:                                               # 基本的数据序列和反序列化，并将信息保存到文件存储
    import pickle as pickle
except ImportError:
    import pickle

import PythonSpider


class DiskCache:
    """
    Dictionary interface that stores cached 
    values in the file system rather than in memory.
    The file path is formed from an md5 hash of the key.

    >>> cache = DiskCache()
    >>> url = 'http://example.webscraping.com'
    >>> result = {'html': '...'}
    >>> cache[url] = result
    >>> cache[url]['html'] == result['html']
    True
    >>> cache = DiskCache(expires=timedelta())
    >>> cache[url] = result
    >>> cache[url]
    Traceback (most recent call last):
     ...
    KeyError: 'http://example.webscraping.com has expired'
    >>> cache.clear()
    """

    def __init__(self, cache_dir='cache', expires=timedelta(seconds=1), compress=True):
        """
        cache_dir: the root level folder for the cache
        expires: timedelta of amount of time before a cache entry is considered expired
        compress: whether to compress data in the cache
        """
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress

    
    def __getitem__(self, url):
        """Load data from disk for this URL
        """
        path = self.url_to_path(url)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                data = fp.read()
                if self.compress:
                    data = zlib.decompress(data) #解压被压缩的缓存数据
                result, timestamp = pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url + ' has expired')
                return result
        else:
            # URL has not yet been cached
            raise KeyError(url + ' does not exist')


    def __setitem__(self, url, result):
        """Save data to disk for this url
        """
        path = self.url_to_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        data = pickle.dumps((result, datetime.utcnow()))
        if self.compress:
            data = zlib.compress(data) #缓存压缩，节省磁盘空间
        with open(path, 'wb') as fp:
            fp.write(data)


    def __delitem__(self, url):
        """Remove the value at this key and any empty parent sub-directories
        """
        path = self._key_path(url)
        try:
            os.remove(path)
            os.removedirs(os.path.dirname(path))
        except OSError:
            pass


    def url_to_path(self, url):
        """Create file system path for this URL
        """
        components = urllib.parse.urlsplit(url)
        # when empty path set to /index.html
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        # replace invalid characters
        filename = re.sub('[^/0-9a-zA-Z\-.,;_ ]', '_', filename)
        # restrict maximum number of characters
        filename = '/'.join(segment[:255] for segment in filename.split('/'))
        return os.path.join(self.cache_dir, filename)


    def has_expired(self, timestamp):
        """Return whether this timestamp has expired
        """
        return datetime.utcnow() > timestamp + self.expires


    def clear(self):
        """Remove all the cached values
        """
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

#if __name__ == '__main__':
#    link_crawler('http://example.webscraping.com/', '/(index|view)', cache=DiskCache())
