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


import argparse
import json
import sys


from arroyo import (
    core,
    scraper
)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)

    fetch_cmd = commands.add_parser('fetch')
    fetch_cmd.add_argument(
        '--provider',
        help='Force some provider'
    )
    fetch_cmd.add_argument(
        '--uri',
        help='URI to parse'
    )
    fetch_cmd.add_argument(
        '--output',
        type=argparse.FileType('wb'),
        default=sys.stdout
    )

    parse_cmd = commands.add_parser('parse')
    parse_cmd.add_argument(
        '--provider',
        required=True)
    parse_cmd.add_argument(
        '--input',
        type=argparse.FileType('rb'),
        required=True)
    parse_cmd.add_argument(
        '--type',
        help='Force type')
    parse_cmd.add_argument(
        '--language',
        help='Force language')

    args = parser.parse_args(sys.argv[1:])

    if args.command == 'fetch':
        do_fetch(fetch_cmd, args)

    elif args.command == 'parse':
        do_parse(fetch_cmd, args)

    else:
        parser.print_help()
        parser.exit(1)


def do_fetch(parser, args):
    if not args.provider and not args.uri:
        parser.print_help()
        parser.exit(1)

    loader = core.Loader()
    engine = scraper.Engine()
    ctx = scraper.build_context(loader, args.provider, args.uri)
    result = engine.fetch_one(ctx)
    args.output.write(result)


def do_parse(parser, args):
    engine = scraper.Engine()
    ctx = scraper.build_context(core.Loader(), args.provider,
                                type=args.type, language=args.language)
    buffer = args.input.read()

    results = list(engine.parse_one(ctx, buffer))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()