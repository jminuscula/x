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


import arroyo
from arroyo import extensions


import asyncio
import sys


import aiohttp


class Context:
    def __init__(self, provider, uri=None, type=None, language=None):
        self.provider = provider
        self.uri = uri or provider.DEFAULT_URI
        self.type = type
        self.language = language

    @property
    def provider_name(self):
        return self.provider.__class__.__name__.lower()

    def __repr__(self):
        data = [
            ("provider", self.provider_name),
            ("uri", self.uri),
            ("type", self.type),
            ("language", self.language),
        ]
        datastr = ", ".join([
            "%s='%s'" % (x[0], x[1])
            for x in data])

        fmt = "<{clsname} {data} at {hexid}"
        return fmt.format(
            clsname=self.__class__.__name__,
            data=datastr,
            hexid=hex(id(self)))


class Engine:
    CLIENT_USER_AGENT = ('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) '
                         'Gecko/20100101 Firefox/69.0')
    CLIENT_TIMEOUT = 15
    CLIENT_MAX_PARALEL_REQUESTS = 5

    def process(self, *ctxs):
        ctxs_and_buffers = self.fetch(*ctxs)
        results = self.parse(*ctxs_and_buffers)

        return results

    def fetch(self, *ctxs):
        async def _task(acc, ctx, sess, sem):
            async with sem:
                try:
                    content = await ctx.provider.fetch(sess, ctx.uri)
                except asyncio.TimeoutError:
                    print("Timeout for '{uri}'".format(uri=ctx.uri), file=sys.stderr)
                    content = ''

                acc.append((ctx, content))

        async def _wrapper(ctxs):
            sess_opts = {
                'cookie_jar': aiohttp.CookieJar(),
                'headers': {
                    'User-Agent': self.CLIENT_USER_AGENT
                },
                'timeout': aiohttp.ClientTimeout(total=self.CLIENT_TIMEOUT)
            }

            ret = []
            sem = asyncio.Semaphore(self.CLIENT_MAX_PARALEL_REQUESTS)

            async with aiohttp.ClientSession(**sess_opts) as sess:
                tasks = [_task(ret, ctx, sess, sem) for ctx in ctxs]
                await asyncio.gather(*tasks)

            return ret

        return asyncio.run(_wrapper(ctxs))

    def fetch_one(self, ctx):
        ctx, content = self.fetch(ctx)[0]
        return content

    def parse(self, *ctxs_and_buffers):
        ret = []

        for (ctx, buffer) in ctxs_and_buffers:
            try:
                ret.extend([self._fix_item(ctx, x)
                            for x in ctx.provider.parse(buffer)])
            except Exception as e:
                print(repr(e))

        return ret

    def parse_one(self, ctx, buffer):
        yield from self.parse((ctx, buffer))

    def _fix_item(self, ctx, item):
        item['provider'] = ctx.provider_name

        if ctx.type:
            item['type'] = ctx.type
        if ctx.language:
            item['language'] = ctx.language

        return item


class ProviderMissingError(Exception):
    pass


def build_context(loader, provider=None, uri=None, type=None, language=None):
    if not isinstance(loader, arroyo.Loader):
        raise TypeError(loader)

    if not provider and not uri:
        errmsg = "Either provider or uri must be specified"
        raise ValueError(errmsg)

    if provider is None:
        for name in loader.list('providers'):
            cls = loader.get_class(name)
            if cls.can_handle(uri):
                provider = cls()
                break
        else:
            raise ProviderMissingError(uri)

    elif isinstance(provider, str):
        provider = loader.get('providers.%s' % (provider))

    if not isinstance(provider, extensions.Provider):
        raise TypeError(provider)

    uri = uri or provider.DEFAULT_URI

    return Context(provider, uri, type=type, language=language)


def build_n_contexts(loader, n, *args, **kwargs):
    def _expand(ctx, n):
        g = ctx.provider.paginate(ctx.uri)
        for _ in range(n):
            try:
                uri = next(g)
            except StopIteration:
                break

            yield Context(provider=ctx.provider, uri=uri,
                          type=ctx.type, language=ctx.language)

    ctx0 = build_context(loader, *args, **kwargs)
    return list(_expand(ctx0, n))
