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


from arroyo import (
    analyze,
    services
)


class Query(dict):
    def __init__(self, **kwargs):
        if 'state' not in kwargs:
            kwargs['state'] = 'none'

        super().__init__(**kwargs)

    @classmethod
    def fromstring(cls, s):
        entity, _, _ = analyze.parse(s)
        params = {k: v for (k, v) in entity.dict().items() if v is not None}
        return cls(**params)


class Engine:
    @property
    def loader(self):
        return services.get_service(services.LOADER)

    def get_sorter(self):
        return self.loader.get('sorters.basic')

    def get_filter(self, name):
        plugins = [self.loader.get(x) for x in self.loader.list('filters')]

        for plugin in plugins:
            if plugin.can_handle(name):
                return plugin

        raise MissingFilterError(name)

    def build_filter(self, query):
        filters = []
        missing = []

        for (key, value) in query.items():
            try:
                f = self.get_filter(key)
            except MissingFilterError:
                missing.append(key)
                continue

            filters.append((f, key, value))

        if missing:
            raise MissingFiltersError(missing)

        return filters

    def apply(self, filters, collection, mp=True):
        ret = collection
        for (f, key, value) in filters:
            ret = f.apply(key, value, ret)

        return ret

    def sort(self, collection):
        groups = {}

        # Group by entity or by source itself
        for source in collection:
            key = source.entity or source
            if key not in groups:
                groups[key] = []

            groups[key].append(source)

        sorter = self.get_sorter()
        ret = [
            (key, sorter.sort(collection))
            for (key, collection) in groups.items()
        ]
        return ret


class MissingFilterError(Exception):
    pass


class MissingFiltersError(MissingFilterError):
    pass
