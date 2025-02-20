# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016-2019 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>
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

import os.path

import pytest

pytest.importorskip('PyQt5.QtWebEngineWidgets')

from glimpsebrowser.browser.webengine import webenginedownloads
from helpers import utils


@pytest.mark.parametrize('path, expected', [
    (os.path.join('subfolder', 'foo'), 'foo'),
    ('foo(1)', 'foo'),
    ('foo (1)', 'foo'),
    ('foo - 1970-01-01T00:00:00.000Z', 'foo'),
    ('foo(a)', 'foo(a)'),
    ('foo1', 'foo1'),
    pytest.param('foo%20bar', 'foo bar', marks=utils.qt58),
    pytest.param('foo%2Fbar', 'bar', marks=utils.qt58),
    pytest.param('foo%20bar', 'foo%20bar', marks=utils.qt59),
    pytest.param('foo%2Fbar', 'foo%2Fbar', marks=utils.qt59),
])
def test_get_suggested_filename(path, expected):
    assert webenginedownloads._get_suggested_filename(path) == expected
