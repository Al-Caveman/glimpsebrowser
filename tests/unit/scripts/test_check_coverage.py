#!/usr/bin/env python3
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2015-2019 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>

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

import sys
import os.path

import pytest

from scripts.dev import check_coverage


pytest_plugins = 'pytester'
pytestmark = [pytest.mark.linux, pytest.mark.not_frozen]


class CovtestHelper:

    """Helper object for covtest fixture.

    Attributes:
        _testdir: The testdir fixture from pytest.
        _monkeypatch: The monkeypatch fixture from pytest.
    """

    def __init__(self, testdir, monkeypatch):
        self._testdir = testdir
        self._monkeypatch = monkeypatch

    def makefile(self, code):
        """Generate a module.py for the given code."""
        self._testdir.makepyfile(module=code)

    def run(self):
        """Run pytest with coverage for the given module.py."""
        coveragerc = str(self._testdir.tmpdir / 'coveragerc')
        self._monkeypatch.delenv('PYTEST_ADDOPTS', raising=False)
        return self._testdir.runpytest('--cov=module',
                                       '--cov-config={}'.format(coveragerc),
                                       '--cov-report=xml',
                                       plugins=['no:faulthandler'])

    def check(self, perfect_files=None):
        """Run check_coverage.py and run its return value."""
        coverage_file = self._testdir.tmpdir / 'coverage.xml'

        if perfect_files is None:
            perfect_files = [(None, 'module.py')]

        argv = [sys.argv[0]]
        self._monkeypatch.setattr(check_coverage.sys, 'argv', argv)

        with self._testdir.tmpdir.as_cwd():
            with coverage_file.open(encoding='utf-8') as f:
                return check_coverage.check(f, perfect_files=perfect_files)

    def check_skipped(self, args, reason):
        """Run check_coverage.py and make sure it's skipped."""
        argv = [sys.argv[0]] + list(args)
        self._monkeypatch.setattr(check_coverage.sys, 'argv', argv)
        with pytest.raises(check_coverage.Skipped) as excinfo:
            return check_coverage.check(None, perfect_files=[])
        assert excinfo.value.reason == reason


@pytest.fixture
def covtest(testdir, monkeypatch):
    """Fixture which provides a coveragerc and a test to call module.func."""
    testdir.makefile(ext='', coveragerc="""
        [run]
        branch=True
    """)
    testdir.makepyfile(test_module="""
        from module import func

        def test_module():
            func()
    """)
    return CovtestHelper(testdir, monkeypatch)


def test_tested_no_branches(covtest):
    covtest.makefile("""
        def func():
            pass
    """)
    covtest.run()
    assert covtest.check() == []


def test_tested_with_branches(covtest):
    covtest.makefile("""
        def func2(arg):
            if arg:
                pass
            else:
                pass

        def func():
            func2(True)
            func2(False)
    """)
    covtest.run()
    assert covtest.check() == []


def test_untested(covtest):
    covtest.makefile("""
        def func():
            pass

        def untested():
            pass
    """)
    covtest.run()
    expected = check_coverage.Message(
        check_coverage.MsgType.insufficient_coverage,
        'module.py',
        'module.py has 75.00% line and 100.00% branch coverage!')
    assert covtest.check() == [expected]


def test_untested_floats(covtest):
    """Make sure we don't report 58.330000000000005% coverage."""
    covtest.makefile("""
        def func():
            pass

        def untested():
            pass

        def untested2():
            pass

        def untested3():
            pass

        def untested4():
            pass

        def untested5():
            pass
    """)
    covtest.run()
    expected = check_coverage.Message(
        check_coverage.MsgType.insufficient_coverage,
        'module.py',
        'module.py has 58.33% line and 100.00% branch coverage!')
    assert covtest.check() == [expected]


def test_untested_branches(covtest):
    covtest.makefile("""
        def func2(arg):
            if arg:
                pass
            else:
                pass

        def func():
            func2(True)
    """)
    covtest.run()
    expected = check_coverage.Message(
        check_coverage.MsgType.insufficient_coverage,
        'module.py',
        'module.py has 100.00% line and 50.00% branch coverage!')
    assert covtest.check() == [expected]


def test_tested_unlisted(covtest):
    covtest.makefile("""
        def func():
            pass
    """)
    covtest.run()
    expected = check_coverage.Message(
        check_coverage.MsgType.perfect_file,
        'module.py',
        'module.py has 100% coverage but is not in perfect_files!')
    assert covtest.check(perfect_files=[]) == [expected]


@pytest.mark.parametrize('args, reason', [
    (['-k', 'foo'], "because -k is given."),
    (['-m', 'foo'], "because -m is given."),
    (['--lf'], "because --lf is given."),
    (['blah', '-m', 'foo'], "because -m is given."),
    (['tests/foo'], "because there is nothing to check."),
])
def test_skipped_args(covtest, args, reason):
    covtest.check_skipped(args, reason)


@pytest.mark.fake_os('windows')
def test_skipped_non_linux(covtest):
    covtest.check_skipped([], "on non-Linux system.")


def _generate_files():
    """Get filenames from WHITELISTED_/PERFECT_FILES."""
    for src_file in check_coverage.WHITELISTED_FILES:
        yield os.path.join('glimpsebrowser', src_file)
    for test_file, src_file in check_coverage.PERFECT_FILES:
        if test_file is not None:
            yield test_file
        yield os.path.join('glimpsebrowser', src_file)


@pytest.mark.parametrize('filename', list(_generate_files()))
def test_files_exist(filename):
    basedir = os.path.join(os.path.dirname(check_coverage.__file__),
                           os.pardir, os.pardir)
    assert os.path.exists(os.path.join(basedir, filename))
