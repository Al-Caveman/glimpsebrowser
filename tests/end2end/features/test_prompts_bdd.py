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

import time

import pytest_bdd as bdd
bdd.scenarios('prompts.feature')

from glimpsebrowser.utils import qtutils


@bdd.when("I load an SSL page")
def load_ssl_page(glimpseproc, ssl_server):
    # We don't wait here as we can get an SSL question.
    glimpseproc.open_path('/', port=ssl_server.port, https=True, wait=False,
                       new_tab=True)


@bdd.when("I wait until the SSL page finished loading")
def wait_ssl_page_finished_loading(glimpseproc, ssl_server):
    glimpseproc.wait_for_load_finished('/', port=ssl_server.port, https=True,
                                    load_status='warn')


@bdd.when("I wait for a prompt")
def wait_for_prompt(glimpseproc):
    glimpseproc.wait_for(message='Asking question *')


@bdd.then("no prompt should be shown")
def no_prompt_shown(glimpseproc):
    glimpseproc.ensure_not_logged(message='Entering mode KeyMode.* (reason: '
                                       'question asked)')


@bdd.then("a SSL error page should be shown")
def ssl_error_page(request, glimpseproc):
    if request.config.webengine and qtutils.version_check('5.9'):
        glimpseproc.wait_for(message="Certificate error: *")
        time.sleep(0.5)  # Wait for error page to appear
        content = glimpseproc.get_content().strip()
        assert ("ERR_INSECURE_RESPONSE" in content or  # Qt <= 5.10
                "ERR_CERT_AUTHORITY_INVALID" in content)  # Qt 5.11
    else:
        if not request.config.webengine:
            line = glimpseproc.wait_for(message='Error while loading *: SSL '
                                     'handshake failed')
            line.expected = True
        glimpseproc.wait_for(message="Changing title for idx * to 'Error "
                          "loading page: *'")
        content = glimpseproc.get_content().strip()
        assert "Unable to load page" in content


class AbstractCertificateErrorWrapper:

    """A wrapper over an SSL/certificate error."""

    def __init__(self, error):
        self._error = error

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def is_overridable(self):
        raise NotImplementedError
