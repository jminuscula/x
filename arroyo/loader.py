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


from arroyo.kit import loader


_plugins = {
    'filters.state':
        'arroyo.plugins.filters.generic.StateFilter',
    'filters.source':
        'arroyo.plugins.filters.generic.SourceAttributeFilter',
    'filters.episode':
        'arroyo.plugins.filters.generic.EpisodeAttributeFilter',
    'filters.movie':
        'arroyo.plugins.filters.generic.MovieAttributeFilter',
    'filters.metadata':
        'arroyo.plugins.filters.generic.MetadataAttributeFilter',

    'providers.eztv':
        'arroyo.plugins.providers.eztv.EzTV',
    'providers.epublibre':
        'arroyo.plugins.providers.epublibre.EPubLibre',
    'providers.torrentapi':
        'arroyo.plugins.providers.torrentapi.TorrentAPI',
    'providers.thepiratebay':
        'arroyo.plugins.providers.thepiratebay.ThePirateBay',

    'sorters.basic':
        'arroyo.plugins.sorters.basic.Basic',

    'downloaders.transmission':
        'arroyo.plugins.downloaders.transmission.Tr'
}


class Loader(loader.ClassLoader):
    def __init__(self):
        super().__init__(_plugins)