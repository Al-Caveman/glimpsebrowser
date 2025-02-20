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

import json
import logging
import re

import pytest
import pytest_bdd as bdd

bdd.scenarios('history.feature')


@pytest.fixture(autouse=True)
def turn_on_sql_history(glimpseproc):
    """Make sure SQL writing is enabled for tests in this module."""
    glimpseproc.send_cmd(":debug-pyeval objreg.get('args')."
                      "debug_flags.remove('no-sql-history')")
    glimpseproc.wait_for_load_finished_url('glimpse://pyeval')


@bdd.then(bdd.parsers.parse("the query parameter {name} should be set to "
                            "{value}"))
def check_query(glimpseproc, name, value):
    """Check if a given query is set correctly.

    This assumes we're on the server query page.
    """
    content = glimpseproc.get_content()
    data = json.loads(content)
    print(data)
    assert data[name] == value


@bdd.then(bdd.parsers.parse("the history should contain:\n{expected}"))
def check_history(glimpseproc, server, tmpdir, expected):
    path = tmpdir / 'history'
    glimpseproc.send_cmd(':debug-dump-history "{}"'.format(path))
    glimpseproc.wait_for(category='message', loglevel=logging.INFO,
                      message='Dumped history to {}'.format(path))

    with path.open('r', encoding='utf-8') as f:
        # ignore access times, they will differ in each run
        actual = '\n'.join(re.sub('^\\d+-?', '', line).strip() for line in f)

    expected = expected.replace('(port)', str(server.port))
    assert actual == expected


@bdd.then("the history should be empty")
def check_history_empty(glimpseproc, server, tmpdir):
    check_history(glimpseproc, server, tmpdir, '')
