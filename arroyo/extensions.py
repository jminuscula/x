# -*- coding: utf-8 -*-

# Copyright (C) 2015 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


import abc
import fnmatch
import re
import sys
import typing

import bs4


class Command:
    COMMAND_NAME: str

    def configure_command(self, cmd):
        pass

    @abc.abstractmethod
    def run(self, ctx, args):
        raise NotImplementedError()


class Provider:
    DEFAULT_URI: str
    URI_GLOBS: typing.List[str] = []
    URI_REGEXPS: typing.List[str] = []

    @classmethod
    def can_handle(cls, url):
        for glob in cls.URI_GLOBS:
            if fnmatch.fnmatch(url, glob):
                return True

        for regexp in cls.URI_REGEXPS:
            if re.search(regexp, url):
                return True

        return False

    def paginate(self, url):
        yield url

    async def fetch(self, sess, uri):
        async with sess.get(uri) as resp:
            return await resp.text()

    def parse(self, buffer):
        return []

    def parse_as_soup(self, buffer):
        return bs4.BeautifulSoup(buffer, "html.parser")

    def get_query_uri(self, query):
        return None


class Filter:
    HANDLES: typing.List[str] = []

    @classmethod
    def can_handle(cls, key):
        return key in cls.HANDLES

    @abc.abstractmethod
    def filter(self, key, value, item):
        raise NotImplementedError()

    def apply(self, key, value, collection):
        return list([item for item in collection
                     if self.filter(key, value, item)])


class Sorter:
    @abc.abstractmethod
    def sort(self, collection):
        raise NotImplementedError()


class Downloader:
    @abc.abstractmethod
    def add(self, source):
        raise NotImplementedError()

    @abc.abstractmethod
    def cancel(self, identifier):
        raise NotImplementedError()

    @abc.abstractmethod
    def archive(self, identifier):
        raise NotImplementedError()

    @abc.abstractmethod
    def remove(self, identifier, delete_data):
        raise NotImplementedError()

    @abc.abstractmethod
    def list(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def dump(self):
        raise NotImplementedError()


class ExtensionError(Exception):
    pass
