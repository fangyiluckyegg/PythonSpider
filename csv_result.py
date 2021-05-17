import re                                         # 字符串匹配模块，正则表达式   
import csv                                        # csv文件操纵
import lxml.html                                  # 解析html格式文件

class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('countries.csv', 'w', newline='')) # 增加newline=''，消除了EXECL打开后的空行
        self.fields = ('area', 'population', 'iso', 'country', 'capital', 'continent', 'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'neighbours')
        self.writer.writerow(self.fields)
 
    def __call__(self, url, html):
        if re.search('/places/', url):
            tree = lxml.html.fromstring(html)
            row = []
            for field in self.fields:
                row.append(tree.cssselect('table>tr#places_{}__row>td.w2p_fw'.format(field))[0].text_content())
            self.writer.writerow(row) #疑难点记录：在for或者if 逻辑下，不同缩进都会有不同的结果。

