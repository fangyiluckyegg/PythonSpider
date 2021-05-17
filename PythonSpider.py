import re                                         # 字符串匹配模块，正则表达式
import urllib.parse                               # 实现url的各种抽取、解析。
import urllib.robotparser                         # 用它对网站的 Robots 协议进行分析

import csv                                        # csv文件操纵
import zipfile                                    # zip格式编码的压缩和解压缩
import io                                         # 处理各种类型I/O的主要工具,包括文本I/O，二进制I/O和原始I/O
import _locale                                    # 为计算机上提供了国际化和本地化转化的环境
import time                                       # 用于处理时间问题,提供操作时间的函数
import sys                                        # sys.argv提供命令行参数传递操作
import queue                                      # 基于多线程的队列管理
import threading                                  # 提供高级的线程接口
import multiprocessing                            # 提供多进程的操作接口

import mongo_queue                                # 导入自定义模块mongo_queue.py
import downloader                                 # 导入自定义模块downloade.py
import mongo_cache                                # 导入自定义模块mongo_cache.py
import disk_cache                                 # 导入自定义模块disk_cache.py
import mongo_result                               # 导入自定义模块mongo_result.py
import csv_result                                 # 导入自定义模块csv_result.py

_locale._getdefaultlocale = (lambda *args: ['zh_CN', 'utf8'])#环境配置默认编码类型utf8

def threaded_crawler(seed_url, link_regex=None, delay=3, user_agent='wswp', proxy=None, num_retries=1, timeout=60, max_depth=2, max_urls=7, html_cache=None, scrape_callback=None, max_threads=10, thread_interval=2):
    """
    seed_url：设置爬取起始地址
    link_regex：设置爬取地址所需要符合的正则表达式（设置过滤条件控制爬取范围），如/(places|view)就是选取爬取地址中有/places或/view的地址

    delay：设置访问时延，传递给downloader.Throttle(delay)【要符合目标网站（robots.txt）的规定，否则可能被封禁】
    user_agent：设置用户代理，传递给downloader.Downloader【要与目标网站（robots.txt）不同意的的用户不一致，否则可能被封禁】
    proxy：支持代理访问某个网站，传递给downloader.Downloader
    num_retries：设置重试下载次数，传递给downloader.Downloader
    timeout:设置网页链接超时时限，传递给downloader.Downloader

    max_depth：基于数据库队列模式的缘故（未用数组模式），暂未使用【设置爬虫深度，避免爬虫陷阱-无限链接，如想禁用，设置为一个负数即可（即当前深度永远不会与之相等）】
    max_urls：基于数据库队列模式的缘故（未用数组模式），暂未使用。

    html_cache：设置网页内容下载并缓存方法（可以是磁盘缓存或数据库缓存）:mongo_cache.py为缓存到数据库；disk_cache.py缓存到磁盘
    scrape_callback：设置网页内容解析并储存方法（可以是函数、类和外部类）:mongo_result.py为解析结果到数据库；csv_result解析结果到文件
   
    max_threads：设置线程启动数量
    thread_interval：设置线程启动间隔时间
    """
    crawl_queue = mongo_queue.MongoQueue()
    crawl_queue.clear()
    crawl_queue.push(seed_url)

    rp = get_robots(seed_url)
    throttle = downloader.Throttle(delay)

    D = downloader.Downloader(delay=delay, user_agent=user_agent, proxies=proxy, num_retries=num_retries, timeout=timeout, cache=html_cache) 

    def process_queue():
        while True:
            # keep track that are processing url
            try:
                url = crawl_queue.pop()
            except KeyError:
                # currently no urls to process
                break
            else:
                if rp.can_fetch(user_agent, url):
                    throttle.wait(url) #等待
                
                    html = D(url)
                    links = [] 
                    if scrape_callback:
#                       links.extend(scrape_callback(url, html) or [])
#                       crawl_queue.complete(url)
                        try:
                           links = scrape_callback(url, html) or []
                        except Exception as e:
                           print ('Error in callback for: {}: {}'.format(url, e))
                        else: 
                            if link_regex:
                                links.extend(link for link in get_links(html) if re.match(link_regex, link)) 
                                for link in links:
                                    # add this new link to queue
                                    crawl_queue.push(normalize(seed_url, link))
                        crawl_queue.complete(url)
                else:
                    print ('Blocked by robots.txt:', url)

    # wait for all download threads to finish
    thread_no = 0
    threads = []
    while threads or crawl_queue:
        for thread in threads:
            if not thread.is_alive():
                threads.remove(thread)
                thread_no=thread_no-1
                print ('线程数量-1',thread_no)
        while len(threads) < max_threads and crawl_queue.peek():            
            # can start some more threads
            thread = threading.Thread(target=process_queue)
            thread.setDaemon(True) # set daemon so main thread can exit when receives ctrl-c
            thread.start()
            thread_no=thread_no+1
            print ('线程数量+1',thread_no)
            threads.append(thread)
            time.sleep(thread_interval)

def normalize(seed_url, link):
    """Normalize this URL by removing hash and adding domain
    """
    link, _ = urllib.parse.urldefrag(link) # remove hash to avoid duplicates
    return urllib.parse.urljoin(seed_url, link)

def same_domain(url1, url2):
    """Return True if both URL's belong to same domain
    """
    return urllib.parse.urlparse(url1).netloc == urllib.parse.urlparse(url2).netloc

def get_robots(url):
    """Initialize robots parser for this domain（初始化获取robots.txt）
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp
    
def get_links(html):
    """Return a list of links from html 
    """
    # a regular expression to extract all links from the webpage/通过正则表达式取出href=所有网络连接地址，re.IGNORECASE-忽略大小写
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(str(html))

def target_depot():
    max_urls = 5
    D = downloader.Downloader()
    zipped_data = D('http://www.luckyegg.net/places/top-1mcsv.zip')
    urls = [] # top 1 million URL's will be stored in this list
    with zipfile.ZipFile(io.BytesIO(zipped_data)) as zf:
        csv_filename = zf.namelist()[0]
        for _, website in csv.reader(io.TextIOWrapper(zf.open(csv_filename))):
            urls.append('http://' + website)
            if len(urls) == max_urls:
                break
            print ('目标网站:', len(urls),website )
    return urls

def process_crawler(args, **kwargs):
    num_cpus = multiprocessing.cpu_count()
    #pool = multiprocessing.Pool(processes=num_cpus)
    print ('Starting {} processes'.format(num_cpus))
    html_cache1=mongo_cache.MongoCache()
    html_cache1.clear()
    mongo_result1=mongo_result.MongoResult()
    mongo_result1.clear()

    processes = []
    for i in range(num_cpus):
        p = multiprocessing.Process(target=threaded_crawler(seed_url=target_url, link_regex='/(places|view)', scrape_callback=mongo_result1, html_cache=html_cache1).run, args=[args], kwargs=kwargs)
        #parsed = pool.apply_async(threaded_link_crawler, args, kwargs)
        p.start()
        processes.append(p)
    # wait for processes to complete
    for p in processes:
        p.join()

if __name__ == '__main__':
     targetdepot = target_depot()
     while targetdepot:
        target_url = targetdepot.pop()
#        threaded_crawler(target_url, '/(places|view)', scrape_callback=mongo_result1, html_cache=html_cache1)
        args_import = int(sys.argv[1])
        process_crawler(args=args_import)
#        process_crawler(seed_url=target_url, scrape_callback=mongo_result1, cache=html_cache1, max_threads=max_threads1, args=1)
