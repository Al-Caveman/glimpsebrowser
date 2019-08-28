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

"""Test starting glimpsebrowser with special arguments/environments."""

import subprocess
import socket
import sys
import logging
import re

import pytest
from PyQt5.QtCore import QProcess, qVersion

from helpers import utils


ascii_locale = pytest.mark.skipif(sys.hexversion >= 0x03070000,
                                  reason="Python >= 3.7 doesn't force ASCII "
                                  "locale with LC_ALL=C")


def _base_args(config):
    """Get the arguments to pass with every invocation."""
    args = ['--debug', '--json-logging', '--no-err-windows']
    if config.webengine:
        args += ['--backend', 'webengine']
    else:
        args += ['--backend', 'webkit']
    if qVersion() == '5.7.1':
        # https://github.com/glimpsebrowser/glimpsebrowser/issues/3163
        args += ['--qt-flag', 'disable-seccomp-filter-sandbox']
    args.append('about:blank')
    return args


@pytest.fixture
def temp_basedir_env(tmpdir, short_tmpdir):
    """Return a dict of environment variables that fakes --temp-basedir.

    We can't run --basedir or --temp-basedir for some tests, so we mess with
    XDG_*_DIR to get things relocated.
    """
    data_dir = tmpdir / 'data'
    config_dir = tmpdir / 'config'
    runtime_dir = short_tmpdir / 'rt'
    cache_dir = tmpdir / 'cache'

    runtime_dir.ensure(dir=True)
    runtime_dir.chmod(0o700)

    lines = [
        '[general]',
        'quickstart-done = 1',
        'backend-warning-shown = 1',
        'old-qt-warning-shown = 1',
        'webkit-warning-shown = 1',
    ]

    state_file = data_dir / 'glimpsebrowser' / 'state'
    state_file.write_text('\n'.join(lines), encoding='utf-8', ensure=True)

    env = {
        'XDG_DATA_HOME': str(data_dir),
        'XDG_CONFIG_HOME': str(config_dir),
        'XDG_RUNTIME_DIR': str(runtime_dir),
        'XDG_CACHE_HOME': str(cache_dir),
    }
    return env


@pytest.mark.linux
@ascii_locale
def test_downloads_with_ascii_locale(request, server, tmpdir, glimpseproc_new):
    """Test downloads with LC_ALL=C set.

    https://github.com/glimpsebrowser/glimpsebrowser/issues/908
    https://github.com/glimpsebrowser/glimpsebrowser/issues/1726
    """
    args = ['--temp-basedir'] + _base_args(request.config)
    glimpseproc_new.start(args, env={'LC_ALL': 'C'})
    glimpseproc_new.set_setting('downloads.location.directory', str(tmpdir))

    # Test a normal download
    glimpseproc_new.set_setting('downloads.location.prompt', 'false')
    url = 'http://localhost:{port}/data/downloads/ä-issue908.bin'.format(
        port=server.port)
    glimpseproc_new.send_cmd(':download {}'.format(url))
    glimpseproc_new.wait_for(category='downloads',
                          message='Download ?-issue908.bin finished')

    # Test :prompt-open-download
    glimpseproc_new.set_setting('downloads.location.prompt', 'true')
    glimpseproc_new.send_cmd(':download {}'.format(url))
    glimpseproc_new.send_cmd(':prompt-open-download "{}" -c pass'
                          .format(sys.executable))
    glimpseproc_new.wait_for(category='downloads',
                          message='Download ä-issue908.bin finished')
    glimpseproc_new.wait_for(category='misc',
                          message='Opening * with [*python*]')

    assert len(tmpdir.listdir()) == 1
    assert (tmpdir / '?-issue908.bin').exists()


@pytest.mark.linux
@pytest.mark.parametrize('url', ['/föö.html', 'file:///föö.html'])
@ascii_locale
def test_open_with_ascii_locale(request, server, tmpdir, glimpseproc_new, url):
    """Test opening non-ascii URL with LC_ALL=C set.

    https://github.com/glimpsebrowser/glimpsebrowser/issues/1450
    """
    args = ['--temp-basedir'] + _base_args(request.config)
    glimpseproc_new.start(args, env={'LC_ALL': 'C'})
    glimpseproc_new.set_setting('url.auto_search', 'never')

    # Test opening a file whose name contains non-ascii characters.
    # No exception thrown means test success.
    glimpseproc_new.send_cmd(':open {}'.format(url))

    if not request.config.webengine:
        line = glimpseproc_new.wait_for(message="Error while loading *: Error "
                                     "opening /*: No such file or directory")
        line.expected = True

    glimpseproc_new.wait_for(message="load status for <* tab_id=* "
                          "url='*/f%C3%B6%C3%B6.html'>: LoadStatus.error")


@pytest.mark.linux
@ascii_locale
def test_open_command_line_with_ascii_locale(request, server, tmpdir,
                                             glimpseproc_new):
    """Test opening file via command line with a non-ascii name with LC_ALL=C.

    https://github.com/glimpsebrowser/glimpsebrowser/issues/1450
    """
    # The file does not actually have to exist because the relevant checks will
    # all be called. No exception thrown means test success.
    args = (['--temp-basedir'] + _base_args(request.config) +
            ['/home/user/föö.html'])
    glimpseproc_new.start(args, env={'LC_ALL': 'C'}, wait_focus=False)

    if not request.config.webengine:
        line = glimpseproc_new.wait_for(message="Error while loading *: Error "
                                     "opening /*: No such file or directory")
        line.expected = True

    glimpseproc_new.wait_for(message="load status for <* tab_id=* "
                          "url='*/f*.html'>: LoadStatus.error")


@pytest.mark.linux
def test_misconfigured_user_dirs(request, server, temp_basedir_env,
                                 tmpdir, glimpseproc_new):
    """Test downloads with a misconfigured XDG_DOWNLOAD_DIR.

    https://github.com/glimpsebrowser/glimpsebrowser/issues/866
    https://github.com/glimpsebrowser/glimpsebrowser/issues/1269
    """
    home = tmpdir / 'home'
    home.ensure(dir=True)
    temp_basedir_env['HOME'] = str(home)

    assert temp_basedir_env['XDG_CONFIG_HOME'] == tmpdir / 'config'
    (tmpdir / 'config' / 'user-dirs.dirs').write('XDG_DOWNLOAD_DIR="relative"',
                                                 ensure=True)

    glimpseproc_new.start(_base_args(request.config), env=temp_basedir_env)

    glimpseproc_new.set_setting('downloads.location.prompt', 'false')
    url = 'http://localhost:{port}/data/downloads/download.bin'.format(
        port=server.port)
    glimpseproc_new.send_cmd(':download {}'.format(url))
    line = glimpseproc_new.wait_for(
        loglevel=logging.ERROR, category='message',
        message='XDG_DOWNLOAD_DIR points to a relative path - please check '
                'your ~/.config/user-dirs.dirs. The download is saved in your '
                'home directory.')
    line.expected = True
    glimpseproc_new.wait_for(category='downloads',
                          message='Download download.bin finished')

    assert (home / 'download.bin').exists()


def test_no_loglines(request, glimpseproc_new):
    """Test glimpse://log with --loglines=0."""
    glimpseproc_new.start(args=['--temp-basedir', '--loglines=0'] +
                       _base_args(request.config))
    glimpseproc_new.open_path('glimpse://log')
    assert glimpseproc_new.get_content() == 'Log output was disabled.'


@pytest.mark.not_frozen
@pytest.mark.parametrize('level', ['1', '2'])
def test_optimize(request, glimpseproc_new, capfd, level):
    glimpseproc_new.start(args=['--temp-basedir'] + _base_args(request.config),
                       env={'PYTHONOPTIMIZE': level})
    if level == '2':
        msg = ("Running on optimize level higher than 1, unexpected behavior "
               "may occur.")
        line = glimpseproc_new.wait_for(message=msg)
        line.expected = True

    # Waiting for quit to make sure no other warning is emitted
    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()


@pytest.mark.not_frozen
@pytest.mark.flaky  # Fails sometimes with empty output...
def test_version(request):
    """Test invocation with --version argument."""
    args = ['-m', 'glimpsebrowser', '--version'] + _base_args(request.config)
    # can't use glimpseproc_new here because it's confused by
    # early process termination
    proc = QProcess()
    proc.setProcessChannelMode(QProcess.SeparateChannels)

    proc.start(sys.executable, args)
    ok = proc.waitForStarted(2000)
    assert ok
    ok = proc.waitForFinished(10000)

    stdout = bytes(proc.readAllStandardOutput()).decode('utf-8')
    print(stdout)
    stderr = bytes(proc.readAllStandardError()).decode('utf-8')
    print(stderr)

    assert ok
    assert proc.exitStatus() == QProcess.NormalExit

    assert re.search(r'^glimpsebrowser\s+v\d+(\.\d+)', stdout) is not None


def test_qt_arg(request, glimpseproc_new, tmpdir):
    """Test --qt-arg."""
    args = (['--temp-basedir', '--qt-arg', 'stylesheet',
             str(tmpdir / 'does-not-exist')] + _base_args(request.config))
    glimpseproc_new.start(args)

    msg = 'QCss::Parser - Failed to load file  "*does-not-exist"'
    line = glimpseproc_new.wait_for(message=msg)
    line.expected = True

    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()


@utils.skip_qt511
def test_webengine_inspector(request, glimpseproc_new):
    if not request.config.webengine:
        pytest.skip()
    args = (['--temp-basedir', '--enable-webengine-inspector'] +
            _base_args(request.config))
    glimpseproc_new.start(args)
    line = glimpseproc_new.wait_for(
        message='Remote debugging server started successfully. Try pointing a '
                'Chromium-based browser to http://127.0.0.1:*')
    port = int(line.message.split(':')[-1])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    s.close()


@pytest.mark.linux
def test_webengine_download_suffix(request, glimpseproc_new, tmpdir):
    """Make sure QtWebEngine does not add a suffix to downloads."""
    if not request.config.webengine:
        pytest.skip()

    download_dir = tmpdir / 'downloads'
    download_dir.ensure(dir=True)

    (tmpdir / 'user-dirs.dirs').write(
        'XDG_DOWNLOAD_DIR={}'.format(download_dir))
    env = {'XDG_CONFIG_HOME': str(tmpdir)}
    args = (['--temp-basedir'] + _base_args(request.config))
    glimpseproc_new.start(args, env=env)

    glimpseproc_new.set_setting('downloads.location.prompt', 'false')
    glimpseproc_new.set_setting('downloads.location.directory', str(download_dir))
    glimpseproc_new.open_path('data/downloads/download.bin', wait=False)
    glimpseproc_new.wait_for(category='downloads', message='Download * finished')
    glimpseproc_new.open_path('data/downloads/download.bin', wait=False)
    glimpseproc_new.wait_for(message='Entering mode KeyMode.yesno *')
    glimpseproc_new.send_cmd(':prompt-accept yes')
    glimpseproc_new.wait_for(category='downloads', message='Download * finished')

    files = download_dir.listdir()
    assert len(files) == 1
    assert files[0].basename == 'download.bin'


def test_command_on_start(request, glimpseproc_new):
    """Make sure passing a command on start works.

    See https://github.com/glimpsebrowser/glimpsebrowser/issues/2408
    """
    args = (['--temp-basedir'] + _base_args(request.config) +
            [':quickmark-add https://www.example.com/ example'])
    glimpseproc_new.start(args)
    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()


def test_launching_with_python2():
    try:
        proc = subprocess.run(['python2', '-m', 'glimpsebrowser',
                               '--no-err-windows'], stderr=subprocess.PIPE)
    except FileNotFoundError:
        pytest.skip("python2 not found")
    assert proc.returncode == 1
    error = "At least Python 3.5 is required to run glimpsebrowser"
    assert proc.stderr.decode('ascii').startswith(error)


def test_initial_private_browsing(request, glimpseproc_new):
    """Make sure the initial window is private when the setting is set."""
    args = (_base_args(request.config) +
            ['--temp-basedir', '-s', 'content.private_browsing', 'true'])
    glimpseproc_new.start(args)

    glimpseproc_new.compare_session("""
        windows:
            - private: True
              tabs:
              - history:
                - url: about:blank
    """)

    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()


def test_loading_empty_session(tmpdir, request, glimpseproc_new):
    """Make sure loading an empty session opens a window."""
    session = tmpdir / 'session.yml'
    session.write('windows: []')

    args = _base_args(request.config) + ['--temp-basedir', '-r', str(session)]
    glimpseproc_new.start(args)

    glimpseproc_new.compare_session("""
        windows:
            - tabs:
              - history:
                - url: about:blank
    """)

    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()


def test_glimpse_settings_persistence(short_tmpdir, request, glimpseproc_new):
    """Make sure settings from glimpse://settings are persistent."""
    args = _base_args(request.config) + ['--basedir', str(short_tmpdir)]
    glimpseproc_new.start(args)
    glimpseproc_new.open_path('glimpse://settings/')
    glimpseproc_new.send_cmd(':jseval --world main '
                          'cset("search.ignore_case", "always")')
    glimpseproc_new.wait_for(message='No output or error')

    assert glimpseproc_new.get_setting('search.ignore_case') == 'always'

    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()

    glimpseproc_new.start(args)
    assert glimpseproc_new.get_setting('search.ignore_case') == 'always'

    glimpseproc_new.send_cmd(':quit')
    glimpseproc_new.wait_for_quit()
