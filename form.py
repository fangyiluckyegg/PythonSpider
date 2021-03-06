# -*- coding: utf-8 -*-

import urllib
from http import cookiejar
from io import BytesIO
import lxml.html
from PIL import Image
import base64


REGISTER_URL = 'http://example.webscraping.com/places/default/user/register?_next=%2Fplaces%2Fdefault%2Findex'


def extract_image(html):
    tree = lxml.html.fromstring(html)
    img_data = tree.cssselect('div#recaptcha img')[0].get('src')
    # remove data:image/png;base64, header
    img_data = img_data.partition(',')[-1]
    # open('test_.png', 'wb').write(data.decode('base64'))
#    binary_img_data = img_data.decode('base64')
    binary_img_data = base64.b64decode(img_data) 
    file_like = BytesIO(binary_img_data)
    img = Image.open(file_like)
    # img.save('test.png')
    return img

def parse_form(html):
    """extract all input properties from the form
    """
    tree = lxml.html.fromstring(html)
    data = {}
    for e in tree.cssselect('form input'):
        if e.get('name'):
            data[e.get('name')] = e.get('value')
    return data

def register(first_name, last_name, email, password, captcha_fn):
    cj = cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    html = opener.open(REGISTER_URL).read()
    form = parse_form(html)
    form['first_name'] = first_name
    form['last_name'] = last_name
    form['email'] = email
    form['password'] = form['password_two'] = password

    img = extract_image(html)
    captcha = captcha_fn(img)

    form['recaptcha_response_field'] = captcha
    encoded_data = urllib.parse.urlencode(form).encode(encoding='UTF8')
#    print(encoded_data)
    request = urllib.request.Request(REGISTER_URL, encoded_data)
    response = opener.open(request)
    success = '/user/register' not in response.geturl()
#    print(response.geturl())
    return success

