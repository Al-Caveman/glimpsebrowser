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

import pytest

import pytest_bdd as bdd


bdd.scenarios('yankpaste.feature')


@pytest.fixture(autouse=True)
def init_fake_clipboard(glimpseproc):
    """Make sure the fake clipboard will be used."""
    glimpseproc.send_cmd(':debug-set-fake-clipboard')


@bdd.when(bdd.parsers.parse('I insert "{value}" into the text field'))
def set_text_field(glimpseproc, value):
    glimpseproc.send_cmd(":jseval --world=0 set_text('{}')".format(value))
    glimpseproc.wait_for_js('textarea set to: ' + value)
