# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2016-2019 Ryan Roden-Corrent (rcorre) <ryan@rcorre.net>
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

import pytest

import pytest_bdd as bdd
bdd.scenarios('marks.feature')


@pytest.fixture(autouse=True)
def turn_on_scroll_logging(glimpseproc):
    """Make sure all scrolling changes are logged."""
    glimpseproc.send_cmd(":debug-pyeval -q objreg.get('args')."
                      "debug_flags.append('no-scroll-filtering')")


@bdd.then(bdd.parsers.parse("the page should be scrolled to {x} {y}"))
def check_y(request, glimpseproc, x, y):
    data = glimpseproc.get_session()
    pos = data['windows'][0]['tabs'][0]['history'][-1]['scroll-pos']
    assert int(x) == pos['x']
    assert int(y) == pos['y']
