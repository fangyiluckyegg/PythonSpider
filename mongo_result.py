from datetime import datetime, timedelta
import pymongo                                          # MongoDB操作工具                      
import lxml.html                                  # 解析html格式文件
import re      


class MongoResult:    
    def __init__(self, client=None):
        self.client = pymongo.MongoClient('localhost', 27017) if client is None else client
        self.db = self.client.cache
#        self.db.result.create_index('timestamp', expireAfterSeconds=expires.total_seconds())
        self.fields = ('area', 'population', 'iso', 'country', 'capital', 'continent', 'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'neighbours')
#       self.writer.writerow(self.fields) 

    def __call__(self, url, html):
        if re.search('/view/', url):
            tree = lxml.html.fromstring(html)
            row = []
            for field in self.fields:
                row.append(tree.cssselect('table>tr#places_{}__row>td.w2p_fw'.format(field))[0].text_content())
            id = self.db.result.find_one({'_id': url})
            record = {'result':row, 'timestamp': datetime.now()}
            self.db.result.update({'_id': url}, {'$set': record}, upsert=True) 

    def clear(self):
        self.db.result.drop()