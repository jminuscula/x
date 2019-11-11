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


import unittest
import os
import random
import time
from unittest import mock


from arroyo.downloads import (
    Database,
    RawDatabase,
    Downloads,
    State,
    UnknowObjectError
)
from arroyo.services import (
        DOWNLOADS_DB,
        LOADER,
        ClassLoader
)


from testlib import (
    build_source,
    patch_service,
    unpatch_service
)


class DatabaseTest(unittest.TestCase):
    def test_raw_dump_and_load(self):
        src1 = build_source('foo')

        db1 = RawDatabase()
        db1.update('foo', src1, 1)

        db2 = RawDatabase.frombuffer(db1.dump())

        self.assertEqual(db2.get_all_states(),
                         {'foo': 1})

    def test_load_new_database(self):
        path = '/tmp/arroyo-test-%04d' % random.randint(0, 8192)
        db = Database(path)

        self.assertEqual(db.list(), [])
        with self.assertRaises(FileNotFoundError):
            os.remove(path)

    def test_load_previous_database(self):
        path = '/tmp/arroyo-test-%04d' % random.randint(0, 8192)

        db1 = Database(path)
        src = build_source('foo')
        db1.update('id:1', src, State.DOWNLOADING)

        db2 = Database(path)

        self.assertEqual(db1.list(), ['id:1'])
        self.assertEqual(db2.list(), ['id:1'])

        os.remove(path)


class DownloaderTestMixin:
    SLOWDOWN = 0.0

    def setUp(self):
        patch_service(LOADER, ClassLoader({
            'downloader': self.DOWNLOADER_SPEC
        }))
        patch_service(DOWNLOADS_DB, RawDatabase())
        self.downloads = Downloads()

    def tearDown(self):
        unpatch_service(LOADER)
        unpatch_service(DOWNLOADS_DB)

    def wait(self):
        if self.SLOWDOWN:
            time.sleep(self.SLOWDOWN)

    def test_add(self):
        s1 = build_source('foo')

        self.downloads.add(s1)
        self.wait()

        self.assertEqual(self.downloads.list(),
                         [s1])

    def test_add_duplicated(self):
        src1 = build_source('foo')

        self.downloads.add(src1)
        self.wait()

        self.downloads.add(src1)
        self.wait()

        self.assertNotEqual(self.downloads.get_state(src1),
                            None)

        self.assertEqual(self.downloads.list(),
                         [src1])

    def test_archive(self):
        src1 = build_source('foo')

        self.downloads.add(src1)
        self.wait()

        self.downloads.archive(src1)
        self.wait()

        self.assertEqual(self.downloads.get_state(src1),
                         State.ARCHIVED)

        self.assertEqual(self.downloads.list(),
                         [])

    def test_cancel(self):
        src1 = build_source('foo')

        self.downloads.add(src1)
        self.wait()

        self.downloads.cancel(src1)
        self.wait()

        with self.assertRaises(UnknowObjectError):
            self.downloads.get_state(src1)

        self.assertEqual(self.downloads.list(),
                         [])

    def test_add_duplicated_archived(self):
        src1 = build_source('foo')

        self.downloads.add(src1)
        self.wait()

        self.downloads.archive(src1)
        self.wait()

        self.downloads.add(src1)
        self.wait()

        self.assertNotEqual(self.downloads.get_state(src1),
                            None)

        self.assertEqual(self.downloads.list(),
                         [src1])

    def test_remove_unknown_source(self):
        src1 = build_source('foo')
        src2 = build_source('bar')

        with self.assertRaises(UnknowObjectError):
            self.downloads.cancel(src1)

        with self.assertRaises(UnknowObjectError):
            self.downloads.archive(src2)

    def test_unexpected_download_from_plugin(self):
        src1 = build_source('foo')
        src2 = build_source('bar')

        self.downloads.add(src1)
        self.wait()

        fake_dump = [
            {'id': self.downloads.db.to_id(src1),
             'state': State.DOWNLOADING},
            {'id': 'external-added-id',
             'state': State.DOWNLOADING}
        ]
        with mock.patch.object(self.downloads.downloader.__class__, 'dump',
                               return_value=fake_dump):
            self.assertEqual(
                self.downloads.list(),
                [src1])

    def test_handle_unexpected_remove_from_plugin_as_cancel(self):
        src1 = build_source('foo')
        src2 = build_source('bar')

        self.downloads.add(src1)
        self.downloads.add(src2)
        self.wait()

        fake_dump = [
            {'id': self.downloads.db.to_id(src1),
             'state': State.DOWNLOADING},
        ]
        with mock.patch.object(self.downloads.downloader.__class__, 'dump',
                               return_value=fake_dump):

            self.assertEqual(
                self.downloads.list(),
                [src1])

            with self.assertRaises(UnknowObjectError):
                self.downloads.get_state(src2)

    def test_handle_unexpected_remove_from_plugin_as_archive(self):
        src1 = build_source('foo')
        src2 = build_source('bar')

        self.downloads.add(src1)
        self.downloads.add(src2)
        self.wait()

        # Manually update state of src2
        id2 = self.downloads.db.to_id(src2)
        self.downloads.db.update(id2, src2, State.SHARING)

        # Mock plugin list to not list src2
        fake_dump = [
            {'id': self.downloads.db.to_id(src1),
             'state': State.DOWNLOADING}
        ]

        with mock.patch.object(self.downloads.downloader.__class__, 'dump',
                               return_value=fake_dump):
            self.assertEqual(
                self.downloads.get_state(src2),
                State.ARCHIVED
            )


class TransmissionTest(DownloaderTestMixin, unittest.TestCase):
    DOWNLOADER_SPEC = 'arroyo.plugins.downloaders.transmission.Tr'
    SLOWDOWN = 0.5

    def tearDown(self):
        transmission = self.downloads.downloader.client

        for x in transmission.get_torrents():
            if x.name in ['foo', 'bar']:
                transmission.remove_torrent(x.id, delete_data=True)

        self.wait()


# class DirectoryTest(DownloaderTestMixin, unittest.TestCase):
#     # TODO:
#     # - Set storage path to tmpdir

#     PLUGINS = ['downloaders.directory']
#     DOWNLOADER = 'directory'
#     SLOWDOWN = 0.2

#     def setUp(self):
#         super().setUp()
#         cls = self.plugin_class()
#         cls._fetch_torrent = mock.Mock(return_value=b'')


if __name__ == '__main__':
    unittest.main()
