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

import os.path

import pytest_bdd as bdd

from helpers import utils

bdd.scenarios('urlmarks.feature')


def _check_marks(glimpseproc, quickmarks, expected, contains):
    """Make sure the given line does (not) exist in the bookmarks.

    Args:
        quickmarks: True to check the quickmarks file instead of bookmarks.
        expected: The line to search for.
        contains: True if the line should be there, False otherwise.
    """
    if quickmarks:
        mark_file = os.path.join(glimpseproc.basedir, 'config', 'quickmarks')
    else:
        mark_file = os.path.join(glimpseproc.basedir, 'config', 'bookmarks',
                                 'urls')

    glimpseproc.clear_data()  # So we don't match old messages
    glimpseproc.send_cmd(':save')
    glimpseproc.wait_for(message='Saved to {}'.format(mark_file))

    with open(mark_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    matched_line = any(
        utils.pattern_match(pattern=expected, value=line.rstrip('\n'))
        for line in lines)

    assert matched_line == contains, lines


@bdd.then(bdd.parsers.parse('the bookmark file should contain "{line}"'))
def bookmark_file_contains(glimpseproc, line):
    _check_marks(glimpseproc, quickmarks=False, expected=line, contains=True)


@bdd.then(bdd.parsers.parse('the bookmark file should not contain "{line}"'))
def bookmark_file_does_not_contain(glimpseproc, line):
    _check_marks(glimpseproc, quickmarks=False, expected=line, contains=False)


@bdd.then(bdd.parsers.parse('the quickmark file should contain "{line}"'))
def quickmark_file_contains(glimpseproc, line):
    _check_marks(glimpseproc, quickmarks=True, expected=line, contains=True)


@bdd.then(bdd.parsers.parse('the quickmark file should not contain "{line}"'))
def quickmark_file_does_not_contain(glimpseproc, line):
    _check_marks(glimpseproc, quickmarks=True, expected=line, contains=False)
