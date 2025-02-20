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

import os
import sys
import shlex

import pytest
import pytest_bdd as bdd
from PyQt5.QtNetwork import QSslSocket
bdd.scenarios('downloads.feature')


PROMPT_MSG = ("Asking question <glimpsebrowser.utils.usertypes.Question "
              "default={!r} mode=<PromptMode.download: 5> option=None "
              "text=* title='Save file to:'>, *")


@bdd.given("I set up a temporary download dir")
def temporary_download_dir(glimpseproc, tmpdir):
    download_dir = tmpdir / 'downloads'
    download_dir.ensure(dir=True)
    glimpseproc.set_setting('downloads.location.prompt', 'false')
    glimpseproc.set_setting('downloads.location.remember', 'false')
    glimpseproc.set_setting('downloads.location.directory', str(download_dir))
    (download_dir / 'subdir').ensure(dir=True)
    try:
        os.mkfifo(str(download_dir / 'fifo'))
    except AttributeError:
        pass
    unwritable = download_dir / 'unwritable'
    unwritable.ensure(dir=True)
    unwritable.chmod(0)


@bdd.given("I clean old downloads")
def clean_old_downloads(glimpseproc):
    glimpseproc.send_cmd(':download-cancel --all')
    glimpseproc.send_cmd(':download-clear')


@bdd.when("SSL is supported")
def check_ssl():
    if not QSslSocket.supportsSsl():
        pytest.skip("QtNetwork SSL not supported")


@bdd.when("the unwritable dir is unwritable")
def check_unwritable(tmpdir):
    unwritable = tmpdir / 'downloads' / 'unwritable'
    if os.access(str(unwritable), os.W_OK):
        # Docker container or similar
        pytest.skip("Unwritable dir was writable")


@bdd.when("I wait until the download is finished")
def wait_for_download_finished(glimpseproc):
    glimpseproc.wait_for(category='downloads', message='Download * finished')


@bdd.when(bdd.parsers.parse("I wait until the download {name} is finished"))
def wait_for_download_finished_name(glimpseproc, name):
    glimpseproc.wait_for(category='downloads',
                      message='Download {} finished'.format(name))


@bdd.when(bdd.parsers.parse('I wait for the download prompt for "{path}"'))
def wait_for_download_prompt(tmpdir, glimpseproc, path):
    full_path = path.replace('(tmpdir)', str(tmpdir)).replace('/', os.sep)
    glimpseproc.wait_for(message=PROMPT_MSG.format(full_path))
    glimpseproc.wait_for(message="Entering mode KeyMode.prompt "
                      "(reason: question asked)")


@bdd.when("I download an SSL page")
def download_ssl_page(glimpseproc, ssl_server):
    glimpseproc.send_cmd(':download https://localhost:{}/'
                      .format(ssl_server.port))


@bdd.then(bdd.parsers.parse("The downloaded file {filename} should not exist"))
def download_should_not_exist(filename, tmpdir):
    path = tmpdir / 'downloads' / filename
    assert not path.check()


@bdd.then(bdd.parsers.parse("The downloaded file {filename} should exist"))
def download_should_exist(filename, tmpdir):
    path = tmpdir / 'downloads' / filename
    assert path.check()


@bdd.then(bdd.parsers.parse("The downloaded file {filename} should be "
                            "{size} bytes big"))
def download_size(filename, size, tmpdir):
    path = tmpdir / 'downloads' / filename
    assert path.size() == int(size)


@bdd.then(bdd.parsers.parse("The downloaded file {filename} should contain "
                            "{text}"))
def download_contents(filename, text, tmpdir):
    path = tmpdir / 'downloads' / filename
    assert text in path.read()


@bdd.then(bdd.parsers.parse('The download prompt should be shown with '
                            '"{path}"'))
def download_prompt(tmpdir, glimpseproc, path):
    full_path = path.replace('(tmpdir)', str(tmpdir)).replace('/', os.sep)
    glimpseproc.wait_for(message=PROMPT_MSG.format(full_path))
    glimpseproc.send_cmd(':leave-mode')


@bdd.when("I set a test python open_dispatcher")
def default_open_dispatcher_python(glimpseproc, tmpdir):
    cmd = '{} -c "import sys; print(sys.argv[1])"'.format(
        shlex.quote(sys.executable))
    glimpseproc.set_setting('downloads.open_dispatcher', cmd)


@bdd.when("I open the download")
def download_open(glimpseproc):
    cmd = '{} -c "import sys; print(sys.argv[1])"'.format(
        shlex.quote(sys.executable))
    glimpseproc.send_cmd(':download-open {}'.format(cmd))


@bdd.when("I open the download with a placeholder")
def download_open_placeholder(glimpseproc):
    cmd = '{} -c "import sys; print(sys.argv[1])"'.format(
        shlex.quote(sys.executable))
    glimpseproc.send_cmd(':download-open {} {{}}'.format(cmd))


@bdd.when("I directly open the download")
def download_open_with_prompt(glimpseproc):
    cmd = '{} -c pass'.format(shlex.quote(sys.executable))
    glimpseproc.send_cmd(':prompt-open-download {}'.format(cmd))


@bdd.when(bdd.parsers.parse("I delete the downloaded file {filename}"))
def delete_file(tmpdir, filename):
    (tmpdir / 'downloads' / filename).remove()


@bdd.then("the FIFO should still be a FIFO")
def fifo_should_be_fifo(tmpdir):
    download_dir = tmpdir / 'downloads'
    assert download_dir.exists()
    assert not os.path.isfile(str(download_dir / 'fifo'))
