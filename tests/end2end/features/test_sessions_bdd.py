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
import logging

import pytest_bdd as bdd
bdd.scenarios('sessions.feature')


@bdd.when(bdd.parsers.parse('I have a "{name}" session file:\n{contents}'))
def create_session_file(glimpseproc, name, contents):
    filename = os.path.join(glimpseproc.basedir, 'data', 'sessions',
                            name + '.yml')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(contents)


@bdd.when(bdd.parsers.parse('I replace "{pattern}" by "{replacement}" in the '
                            '"{name}" session file'))
def session_replace(glimpseproc, server, pattern, replacement, name):
    # First wait until the session was actually saved
    glimpseproc.wait_for(category='message', loglevel=logging.INFO,
                      message='Saved session {}.'.format(name))
    filename = os.path.join(glimpseproc.basedir, 'data', 'sessions',
                            name + '.yml')
    replacement = replacement.replace('(port)', str(server.port))  # yo dawg
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data.replace(pattern, replacement))


@bdd.then(bdd.parsers.parse("the session {name} should exist"))
def session_should_exist(glimpseproc, name):
    filename = os.path.join(glimpseproc.basedir, 'data', 'sessions',
                            name + '.yml')
    assert os.path.exists(filename)


@bdd.then(bdd.parsers.parse("the session {name} should not exist"))
def session_should_not_exist(glimpseproc, name):
    filename = os.path.join(glimpseproc.basedir, 'data', 'sessions',
                            name + '.yml')
    assert not os.path.exists(filename)
