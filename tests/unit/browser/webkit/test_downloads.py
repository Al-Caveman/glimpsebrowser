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

import pytest

from glimpsebrowser.browser import downloads, qtnetworkdownloads


def test_download_model(qapp, qtmodeltester, config_stub, cookiejar_and_cache,
                        fake_args):
    """Simple check for download model internals."""
    manager = qtnetworkdownloads.DownloadManager()
    model = downloads.DownloadModel(manager)
    qtmodeltester.check(model)


@pytest.mark.parametrize('url, title, out', [
    ('http://glimpsebrowser.org/INSTALL.html',
     'Installing glimpsebrowser | glimpsebrowser',
     'Installing glimpsebrowser _ glimpsebrowser.html'),
    ('http://glimpsebrowser.org/INSTALL.html',
     'Installing glimpsebrowser | glimpsebrowser.html',
     'Installing glimpsebrowser _ glimpsebrowser.html'),
    ('http://glimpsebrowser.org/INSTALL.HTML',
     'Installing glimpsebrowser | glimpsebrowser',
     'Installing glimpsebrowser _ glimpsebrowser.html'),
    ('http://glimpsebrowser.org/INSTALL.html',
     'Installing glimpsebrowser | glimpsebrowser.HTML',
     'Installing glimpsebrowser _ glimpsebrowser.HTML'),
    ('http://glimpsebrowser.org/',
     'glimpsebrowser | glimpsebrowser',
     'glimpsebrowser _ glimpsebrowser.html'),
    ('https://github.com/glimpsebrowser/glimpsebrowser/releases',
     'Releases · glimpsebrowser/glimpsebrowser',
     'Releases · glimpsebrowser_glimpsebrowser.html'),
    ('http://glimpsebrowser.org/index.php',
     'glimpsebrowser | glimpsebrowser',
     'glimpsebrowser _ glimpsebrowser.html'),
    ('http://glimpsebrowser.org/index.php',
     'glimpsebrowser | glimpsebrowser - index.php',
     'glimpsebrowser _ glimpsebrowser - index.php.html'),
    ('https://glimpsebrowser.org/img/cheatsheet-big.png',
     'cheatsheet-big.png (3342×2060)',
     None),
    ('http://glimpsebrowser.org/page-with-no-title.html',
     '',
     None),
])
@pytest.mark.fake_os('windows')
def test_page_titles(url, title, out):
    assert downloads.suggested_fn_from_title(url, title) == out


class TestDownloadTarget:

    def test_filename(self):
        target = downloads.FileDownloadTarget("/foo/bar")
        assert target.filename == "/foo/bar"

    def test_fileobj(self):
        fobj = object()
        target = downloads.FileObjDownloadTarget(fobj)
        assert target.fileobj is fobj

    def test_openfile(self):
        target = downloads.OpenFileDownloadTarget()
        assert target.cmdline is None

    def test_openfile_custom_command(self):
        target = downloads.OpenFileDownloadTarget('echo')
        assert target.cmdline == 'echo'

    @pytest.mark.parametrize('obj', [
        downloads.FileDownloadTarget('foobar'),
        downloads.FileObjDownloadTarget(None),
        downloads.OpenFileDownloadTarget(),
    ])
    def test_class_hierarchy(self, obj):
        assert isinstance(obj, downloads._DownloadTarget)


@pytest.mark.parametrize('raw, expected', [
    pytest.param('http://foo/bar', 'bar',
                 marks=pytest.mark.fake_os('windows')),
    pytest.param('A *|<>\\: bear!', 'A ______ bear!',
                 marks=pytest.mark.fake_os('windows')),
    pytest.param('A *|<>\\: bear!', 'A *|<>\\: bear!',
                 marks=[pytest.mark.fake_os('posix'), pytest.mark.posix]),
])
def test_sanitized_filenames(raw, expected,
                             config_stub, download_tmpdir, monkeypatch):
    manager = downloads.AbstractDownloadManager()
    target = downloads.FileDownloadTarget(str(download_tmpdir))
    item = downloads.AbstractDownloadItem()

    # Don't try to start a timer outside of a QThread
    manager._update_timer.isActive = lambda: True

    # Abstract methods
    item._ensure_can_set_filename = lambda *args: True
    item._after_set_filename = lambda *args: True

    manager._init_item(item, True, raw)
    item.set_target(target)
    assert item._filename.endswith(expected)
