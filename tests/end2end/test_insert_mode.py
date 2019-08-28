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

"""Test insert mode settings on html files."""

import pytest


@pytest.mark.parametrize(['file_name', 'elem_id', 'source', 'input_text'], [
    ('textarea.html', 'glimpse-textarea', 'clipboard', 'glimpsebrowser'),
    ('textarea.html', 'glimpse-textarea', 'keypress', 'superglimpsebrowser'),
    ('input.html', 'glimpse-input', 'clipboard', 'amazingglimpsebrowser'),
    ('input.html', 'glimpse-input', 'keypress', 'awesomeglimpsebrowser'),
    ('autofocus.html', 'glimpse-input-autofocus', 'keypress', 'cutebrowser'),
])
@pytest.mark.parametrize('zoom', [100, 125, 250])
def test_insert_mode(file_name, elem_id, source, input_text, zoom,
                     glimpseproc, request):
    url_path = 'data/insert_mode_settings/html/{}'.format(file_name)
    glimpseproc.open_path(url_path)
    glimpseproc.send_cmd(':zoom {}'.format(zoom))

    glimpseproc.send_cmd(':click-element --force-event id {}'.format(elem_id))
    glimpseproc.wait_for(message='Entering mode KeyMode.insert (reason: *)')
    glimpseproc.send_cmd(':debug-set-fake-clipboard')

    if source == 'keypress':
        glimpseproc.press_keys(input_text)
    elif source == 'clipboard':
        glimpseproc.send_cmd(':debug-set-fake-clipboard "{}"'.format(input_text))
        glimpseproc.send_cmd(':insert-text {clipboard}')
    else:
        raise ValueError("Invalid source {!r}".format(source))

    glimpseproc.wait_for_js('contents: {}'.format(input_text))
    glimpseproc.send_cmd(':leave-mode')


@pytest.mark.parametrize('auto_load, background, insert_mode', [
    (False, False, False),  # auto_load disabled
    (True, False, True),  # enabled and foreground tab
    (True, True, False),  # background tab
])
def test_auto_load(glimpseproc, auto_load, background, insert_mode):
    glimpseproc.set_setting('input.insert_mode.auto_load', str(auto_load))
    url_path = 'data/insert_mode_settings/html/autofocus.html'
    glimpseproc.open_path(url_path, new_bg_tab=background)

    log_message = 'Entering mode KeyMode.insert (reason: *)'
    if insert_mode:
        glimpseproc.wait_for(message=log_message)
        glimpseproc.send_cmd(':leave-mode')
    else:
        glimpseproc.ensure_not_logged(message=log_message)


def test_auto_leave_insert_mode(glimpseproc):
    url_path = 'data/insert_mode_settings/html/autofocus.html'
    glimpseproc.open_path(url_path)

    glimpseproc.set_setting('input.insert_mode.auto_leave', 'true')
    glimpseproc.send_cmd(':zoom 100')

    glimpseproc.press_keys('abcd')

    glimpseproc.send_cmd(':hint all')
    glimpseproc.wait_for(message='hints: *')

    # Select the disabled input box to leave insert mode
    glimpseproc.send_cmd(':follow-hint s')
    glimpseproc.wait_for(message='Clicked non-editable element!')


@pytest.mark.parametrize('leave_on_load', [True, False])
def test_auto_leave_insert_mode_reload(glimpseproc, leave_on_load):
    url_path = 'data/hello.txt'
    glimpseproc.open_path(url_path)

    glimpseproc.set_setting('input.insert_mode.leave_on_load',
                         str(leave_on_load).lower())
    glimpseproc.send_cmd(':enter-mode insert')
    glimpseproc.wait_for(message='Entering mode KeyMode.insert (reason: *)')
    glimpseproc.send_cmd(':reload')
    if leave_on_load:
        glimpseproc.wait_for(message='Leaving mode KeyMode.insert (reason: *)')
    else:
        glimpseproc.wait_for(
            message='Ignoring leave_on_load request due to setting.')
