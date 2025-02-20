# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2015-2019 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>
#
# This file is part of glimpsebrowser.
#
# glimpsebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# glimpsebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with glimpsebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Test mhtml downloads based on sample files."""

import os
import os.path
import re
import collections

import pytest

from glimpsebrowser.utils import qtutils


def collect_tests():
    basedir = os.path.dirname(__file__)
    datadir = os.path.join(basedir, 'data', 'downloads', 'mhtml')
    files = os.listdir(datadir)
    return files


def normalize_line(line):
    line = line.rstrip('\n')
    line = re.sub('boundary="-+(=_glimpse|MultipartBoundary)-[0-9a-zA-Z-]+"',
                  'boundary="---=_glimpse-UUID"', line)
    line = re.sub('^-+(=_glimpse|MultipartBoundary)-[0-9a-zA-Z-]+$',
                  '-----=_glimpse-UUID', line)
    line = re.sub(r'localhost:\d{1,5}', 'localhost:(port)', line)
    if line.startswith('Date: '):
        line = 'Date: today'
    if line.startswith('Content-ID: '):
        line = 'Content-ID: 42'

    # Depending on Python's mimetypes module/the system's mime files, .js
    # files could be either identified as x-javascript or just javascript
    line = line.replace('Content-Type: application/x-javascript',
                        'Content-Type: application/javascript')

    # With QtWebKit and newer Werkzeug versions, we also get an encoding
    # specified.
    line = line.replace('javascript; charset=utf-8', 'javascript')

    # Added with Qt 5.11
    if (line.startswith('Snapshot-Content-Location: ') and
            not qtutils.version_check('5.11', compiled=False)):
        line = None

    return line


def normalize_whole(s, webengine):
    if qtutils.version_check('5.12', compiled=False) and webengine:
        s = s.replace('\n\n-----=_glimpse-UUID', '\n-----=_glimpse-UUID')
    return s


class DownloadDir:

    """Abstraction over a download directory."""

    def __init__(self, tmpdir, config):
        self._tmpdir = tmpdir
        self._config = config
        self.location = str(tmpdir)

    def read_file(self):
        files = self._tmpdir.listdir()
        assert len(files) == 1

        with open(str(files[0]), 'r', encoding='utf-8') as f:
            return f.readlines()

    def sanity_check_mhtml(self):
        assert 'Content-Type: multipart/related' in '\n'.join(self.read_file())

    def compare_mhtml(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            expected_data = '\n'.join(normalize_line(line)
                                      for line in f
                                      if normalize_line(line) is not None)
        actual_data = '\n'.join(normalize_line(line)
                                for line in self.read_file())
        actual_data = normalize_whole(actual_data,
                                      webengine=self._config.webengine)

        assert actual_data == expected_data


@pytest.fixture
def download_dir(tmpdir, pytestconfig):
    return DownloadDir(tmpdir, pytestconfig)


def _test_mhtml_requests(test_dir, test_path, server):
    with open(os.path.join(test_dir, 'requests'), encoding='utf-8') as f:
        expected_requests = []
        for line in f:
            if line.startswith('#'):
                continue
            path = '/{}/{}'.format(test_path, line.strip())
            expected_requests.append(server.ExpectedRequest('GET', path))

    actual_requests = server.get_requests()
    # Requests are not hashable, we need to convert to ExpectedRequests
    actual_requests = [server.ExpectedRequest.from_request(req)
                       for req in actual_requests]
    assert (collections.Counter(actual_requests) ==
            collections.Counter(expected_requests))


@pytest.mark.parametrize('test_name', collect_tests())
def test_mhtml(request, test_name, download_dir, glimpseproc, server):
    glimpseproc.set_setting('downloads.location.directory', download_dir.location)
    glimpseproc.set_setting('downloads.location.prompt', 'false')

    test_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'data', 'downloads', 'mhtml', test_name)
    test_path = 'data/downloads/mhtml/{}'.format(test_name)

    url_path = '{}/{}.html'.format(test_path, test_name)
    glimpseproc.open_path(url_path)

    download_dest = os.path.join(download_dir.location,
                                 '{}-downloaded.mht'.format(test_name))

    # Wait for favicon.ico to be loaded if there is one
    if os.path.exists(os.path.join(test_dir, 'favicon.png')):
        server.wait_for(path='/{}/favicon.png'.format(test_path))

    # Discard all requests that were necessary to display the page
    server.clear_data()
    glimpseproc.send_cmd(':download --mhtml --dest "{}"'.format(download_dest))
    glimpseproc.wait_for(category='downloads',
                      message='File successfully written.')

    suffix = '-webengine' if request.config.webengine else ''
    filename = '{}{}.mht'.format(test_name, suffix)
    expected_file = os.path.join(test_dir, filename)
    if os.path.exists(expected_file):
        download_dir.compare_mhtml(expected_file)
    else:
        download_dir.sanity_check_mhtml()

    if not request.config.webengine:
        _test_mhtml_requests(test_dir, test_path, server)
