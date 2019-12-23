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

import logging
from arroyo.kit import cache
from arroyo.extensions import (
    Downloader,
    Filter,
    Provider,
    Sorter,
    ExtensionError
)


class _Services:
    def __init__(self):
        self._cache = cache.NullCache()
        self._loader = None
        self._settings = None
        self._db = None
        self._logger = logging.getLogger('arroyo.services')

    def _setter(self, attr, value):
        logmsg = "Setting service %s to %s"
        logmsg = logmsg % (attr, value)
        self._logger.debug(logmsg)
        setattr(self, '_' + attr, value)

    @property
    def cache(self):
        return self._cache

    @cache.setter
    def cache(self, x):
        self._setter('cache', x)

    @property
    def loader(self):
        return self._loader

    @loader.setter
    def loader(self, x):
        self._setter('loader', x)

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, x):
        self._setter('settings', x)

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, x):
        self._setter('db', x)


services = _Services()


__all__ = [
    'Downloader',
    'Filter',
    'Provider',
    'Sorter',
    'ExtensionError',
    'services'
]
