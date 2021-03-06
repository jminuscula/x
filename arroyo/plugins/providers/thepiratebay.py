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


import re
import sys
import time
from datetime import datetime
from urllib import parse


import humanfriendly


from arroyo import extensions


class _CategoryUnknowError(Exception):
    pass


class ThePirateBay(extensions.Provider):
    # URL structure:
    # https://thepiratebay.cr/search.php?q={q}&page={page}&orderby=99
    # order_by=3 uploaded
    # order_by=5 size
    # order_by=11 uploaded by
    # order_by=7 seeds
    # order_by=9 leechers
    # order_by=11 uploaded by

    PROTO = 'https'
    TLD = 'org'

    DEFAULT_URI = '{proto}://thepiratebay.{tld}/recent/0/'.format(
        proto=PROTO, tld=TLD
    )
    URI_PATTERNS = [
        r'^http(s)?://([^.]+.)?thepiratebay\.[^.]{2,3}/(?!rss/)'
    ]

    SEARCH_URL_PATTERN = (
        "{proto}://thepiratebay.{tld}".format(proto=PROTO, tld=TLD) +
        "/search/{q}/0/99/0"
    )

    _TYPE_TABLE = {
        'applications': {
            'applications': 'other',
            'android': 'other',
            'handheld': 'other',
            'ios (ipad/iphone)': 'other',
            'mac': 'other',
            'other os': 'other',
            'unix': 'other',
            'windows': 'other'
        },
        'audio': {
            'music': 'music',
            'audio books': 'book',
            'sound clips': 'other',
            'flac': 'music',
            'other': 'other'
        },
        'books': {
            'books': 'book'
        },
        'games': {
            'android': 'other',
            'handheld': 'other',
            'ios (ipad/iphone)': 'other',
            'mac': 'other',
            'other': 'other',
            'pc': 'other',
            'psx': 'other',
            'wii': 'other',
            'xbox360': 'other'
        },
        'movies': {
            'movies': 'movie'
        },
        'music': {
            'music': 'music'
        },
        'other': {
            'e-books': 'book',
            'comics': 'other',
            'covers': 'other',
            'other': 'other',
            'physibles(?!)': 'other',
            'pictures': 'other'
        },
        'porn': {
            'movies': 'xxx',
            'games': 'xxx',
            'hd - movies': 'xxx',
            'movie clips': 'xxx',
            'movies dvdr': 'xxx',
            'other': 'xxx',
            'pictures': 'xxx'
        },
        'tv': {
            'tv': 'episode'
        },
        'video': {
            'movies': 'movie',
            'movies dvdr': 'movie',
            'music videos': 'other',
            'Movie clips': 'other',
            'tv shows': 'episode',
            'handheld': 'other',
            'hd - movies': 'movie',
            'hd - tv shows': 'episode',
            '3d': 'other',
            'other': 'other',
        },
        'xxx': {
            'xxx': 'xxx'
        }
    }

    def paginate(self, uri):
        # Add leading '/'
        if not uri.endswith('/'):
            uri += '/'

        # Get page
        try:
            page = int(re.findall(r'/(\d+)/', uri)[0])
        except IndexError:
            page = 0
            uri += '0/'

        pre, post = re.split(r'/\d+/', uri, maxsplit=1)

        while True:
            yield pre + '/' + str(page) + '/' + post
            page += 1

    def parse(self, buff):
        def parse_row(row):
            details = row.select('font.detDesc')[0].text

            # Parse category
            try:
                typ = self.parse_category(row.select('td')[0].text)
            except _CategoryUnknowError as e:
                typ = 'other'
                msg = "Unknow category: '{category}'"
                msg = msg.format(category=e.args[0])
                print(msg, file=sys.stderr)

            # Parse size
            size = re.findall(r'([0-9\.]+\s*[GMK]i?B)',
                              details,
                              re.IGNORECASE)[0]
            size = humanfriendly.parse_size(size)

            # Parse created
            try:
                created = self.parse_timestamp(row.select('.detDesc')[0].text)
            except IndexError:
                created = 'other'

            return {
                'name': row.findAll('a')[2].text,
                'uri': row.findAll('a')[3]['href'],
                'type': typ,
                'size': size,
                'created': created,
                'seeds': int(row.findAll('td')[-2].text),
                'leechers': int(row.findAll('td')[-1].text)
            }

        def filter_row(row):
            return any((link.attrs.get('href', '').startswith('magnet')
                        for link in row.select('a')))

        soup = self.parse_as_soup(buff)
        rows = soup.select('tr')
        rows = filter(filter_row, rows)

        return list(map(parse_row, rows))

    @classmethod
    def parse_category(cls, text):
        cat = text.lower()
        cat = cat.replace('(', '').replace(')', '')
        cat = cat.replace('\n', '\0').replace('\t', '\0').split('\0')
        cat = [x.strip() for x in cat if x]

        try:
            typ = cls._TYPE_TABLE[cat[0]][cat[1]]
        except KeyError:
            raise _CategoryUnknowError(cat[0] + '>' + cat[1])

        return typ

    @classmethod
    def parse_timestamp(cls, text):
        def conv(d):
            keys = now_dt.copy()
            keys.update({k: int(v) for (k, v) in d.items()})

            p = '{Y:04d} {m:02d} {d:02d} {H:02d} {M:02d} {S:02d}'
            p = p.format(**keys)
            p = datetime.strptime(p, '%Y %m %d %H %M %S')

            return int(time.mktime(p.timetuple()))

        now = int(time.mktime(datetime.now().timetuple()))
        now_dt = datetime.now()
        now_dt = dict(
            Y=now_dt.year,
            m=now_dt.month,
            d=now_dt.day,
            H=now_dt.hour,
            M=now_dt.minute,
            S=now_dt.second
        )

        text = text.lower().replace('&nbsp;', ' ')

        # 20 mins ago
        m = re.search(r'(\d+).+?mins', text)
        if m:
            return now - int(m.group(1)) * 60

        # today 13:14
        # yester 15:19
        m = re.search(r'(?P<mod>yester|today).+?(?P<H>\d+):(?P<M>\d+)',
                      text)
        if m:
            d = m.groupdict()
            mod = d.pop('mod')
            x = conv(d)
            return x if mod == 'today' else x - (60*60*24)

        # 07-15 13:34
        m = re.search(r'(?P<m>\d+)-(?P<d>\d+).+?(?P<H>\d+):(?P<M>\d+)',
                      text)
        if m:
            return conv(m.groupdict())

        # 07-15 2004
        m = re.search(r'(?P<m>\d+)-(?P<d>\d+).+?(?P<Y>\d{4})',
                      text)
        if m:
            return conv(m.groupdict())

        return now

    def get_query_uri(self, query):
        q = query.str()
        if not q:
            return

        q = re.sub(r'[^a-zA-Z0-9]', ' ', q)
        q = parse.quote_plus(q)
        return self.SEARCH_URL_PATTERN.format(q=q)
