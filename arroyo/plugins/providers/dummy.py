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


from arroyo import Provider


class RarBG(Provider):
    URI_REGEXPS = [
        r'https?://(www.)?rarbg.com/.*'
    ]


class ThePirateBay(Provider):
    URI_REGEXPS = [
        r'https?://(www.)?thepiratebay.com/.*'
    ]

    def parse(self, buffer):
        soup = self.parse_as_soup(buffer)
        return [soup]
