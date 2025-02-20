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

import pytest_bdd as bdd

from glimpsebrowser.utils import qtutils


bdd.scenarios('glimpsescheme.feature')


@bdd.then(bdd.parsers.parse("the {kind} request should be blocked"))
def request_blocked(request, glimpseproc, kind):
    blocking_set_msg = (
        "Blocking malicious request from glimpse://settings/set?* to "
        "glimpse://settings/set?*")
    blocking_csrf_msg = (
        "Blocking malicious request from "
        "http://localhost:*/data/misc/glimpsescheme_csrf.html to "
        "glimpse://settings/set?*")
    blocking_js_msg = (
        "[http://localhost:*/data/misc/glimpsescheme_csrf.html:0] Not allowed to "
        "load local resource: glimpse://settings/set?*"
    )

    webkit_error_invalid = (
        "Error while loading glimpse://settings/set?*: Invalid glimpse://settings "
        "request")
    webkit_error_unsupported = (
        "Error while loading glimpse://settings/set?*: Unsupported request type")

    if request.config.webengine and qtutils.version_check('5.12'):
        # On Qt 5.12, we mark glimpse:// as a local scheme, causing most requests
        # being blocked by Chromium internally (logging to the JS console).
        expected_messages = {
            'img': [blocking_js_msg],
            'link': [blocking_js_msg],
            'redirect': [blocking_set_msg],
            'form': [blocking_js_msg],
        }
    elif request.config.webengine:
        expected_messages = {
            'img': [blocking_csrf_msg],
            'link': [blocking_set_msg],
            'redirect': [blocking_set_msg],
            'form': [blocking_set_msg],
        }
    else:  # QtWebKit
        expected_messages = {
            'img': [blocking_csrf_msg],
            'link': [blocking_csrf_msg, webkit_error_invalid],
            'redirect': [blocking_csrf_msg, webkit_error_invalid],
            'form': [webkit_error_unsupported],
        }

    for pattern in expected_messages[kind]:
        msg = glimpseproc.wait_for(message=pattern)
        msg.expected = True
