# -*- coding: utf-8 -*-

import json
import string
import downloader
import mongo_cache

FIELDS = ('area', 'population', 'iso', 'country', 'capital', 'continent', 'tld', 'currency_code', 'currency_name', 'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'neighbours')

def main():
    template_url = 'http://example.webscraping.com/ajax/search.json?page={}&page_size=10&search_term={}'
    countries = set()
    html_cache = mongo_cache.MongoCache()
    download = downloader.Downloader(delay=3, num_retries=1, timeout=60, cache=html_cache) 

    for search_term in string.ascii_lowercase:
        page = 1
        while True:
            html = download(template_url.format(page, search_term))
            try:
                ajax = json.loads(html)
            except ValueError as e:
                print (e)
                ajax = None
            else:
                for record in ajax['records']:
                    countries.add(record['country'])
            page += 1
            if ajax is None or page >= ajax['num_pages']:
                break
    
    open('countries.txt', 'w').write('\n'.join(sorted(countries)))

if __name__ == '__main__':
    main()