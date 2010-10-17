#!/usr/bin/env python
# encoding: utf-8

"""A python interface of the Instapaper Read Late API"""

__author__ = 'Eiji Kato <teqnolize at gmail.com>'
__version__ = '0.1'
__homepage__ = 'http://github.com/technolize/python-instapaper/'

import urllib
import instapaper

class InstapaperError(Exception):
    pass

class Instapaper(object):
    def __init__(self, username='', password=''):
        self._username = username
        self._password = password
    
    def auth(self, username='', password=''):
        if username:
            return self._do_auth(username, password)
        if self._username:
            return self._do_auth(self._username, self._password)
        return False
    
    def add(self, url, title='', selection='', auto_title=1):
        api = "https://www.instapaper.com/api/add"
        
        if not url:
            raise InstapaperError("required url")
        
        params = {
            'username': self._username,
            'password': self._password,
            'url': url,
            'title': title,
            'selection': selection,
            'auto-title': auto_title
        }
        params = urllib.urlencode(params)
        f = urllib.urlopen(api, params)
        
        status = f.getcode()
        if status == 201:
            return f.headers['Content-Location']
        elif status == 400:
            raise InstapaperError("bad request. probably missing a required parameter, such as url")
        elif status == 403:
            raise InstapaperError("invalid username or password")
        elif status == 500:
            raise InstapaperError("the service encountered an error")
    
    def _do_auth(self, username, password=''):
        api = 'https://www.instapaper.com/api/authenticate'
        params = urllib.urlencode({
            'username': username,
            'password': password,
        })
        f = urllib.urlopen(api, params)
        status = f.getcode()
        if status == 200:
            return True
        return False
