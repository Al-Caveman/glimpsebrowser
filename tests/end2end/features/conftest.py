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

"""Steps for bdd-like tests."""

import os
import os.path
import re
import sys
import time
import json
import logging
import collections
import textwrap
import subprocess

import pytest
import pytest_bdd as bdd

import glimpsebrowser
from glimpsebrowser.utils import log, utils, docutils
from glimpsebrowser.browser import pdfjs
from helpers import utils as testutils


def _get_echo_exe_path():
    """Return the path to an echo-like command, depending on the system.

    Return:
        Path to the "echo"-utility.
    """
    if utils.is_windows:
        return os.path.join(testutils.abs_datapath(), 'userscripts',
                            'echo.bat')
    else:
        return 'echo'


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add a BDD section to the test output."""
    outcome = yield
    if call.when not in ['call', 'teardown']:
        return
    report = outcome.get_result()

    if report.passed:
        return

    if (not hasattr(report.longrepr, 'addsection') or
            not hasattr(report, 'scenario')):
        # In some conditions (on macOS and Windows it seems), report.longrepr
        # is actually a tuple. This is handled similarly in pytest-qt too.
        #
        # Since this hook is invoked for any test, we also need to skip it for
        # non-BDD ones.
        return

    if sys.stdout.isatty() and item.config.getoption('--color') != 'no':
        colors = {
            'failed': log.COLOR_ESCAPES['red'],
            'passed': log.COLOR_ESCAPES['green'],
            'keyword': log.COLOR_ESCAPES['cyan'],
            'reset': log.RESET_ESCAPE,
        }
    else:
        colors = {
            'failed': '',
            'passed': '',
            'keyword': '',
            'reset': '',
        }

    output = []
    output.append("{kw_color}Feature:{reset} {name}".format(
        kw_color=colors['keyword'],
        name=report.scenario['feature']['name'],
        reset=colors['reset'],
    ))
    output.append(
        "  {kw_color}Scenario:{reset} {name} ({filename}:{line})".format(
            kw_color=colors['keyword'],
            name=report.scenario['name'],
            filename=report.scenario['feature']['rel_filename'],
            line=report.scenario['line_number'],
            reset=colors['reset'])
    )
    for step in report.scenario['steps']:
        output.append(
            "    {kw_color}{keyword}{reset} {color}{name}{reset} "
            "({duration:.2f}s)".format(
                kw_color=colors['keyword'],
                color=colors['failed'] if step['failed'] else colors['passed'],
                keyword=step['keyword'],
                name=step['name'],
                duration=step['duration'],
                reset=colors['reset'])
        )

    report.longrepr.addsection("BDD scenario", '\n'.join(output))


## Given


@bdd.given(bdd.parsers.parse("I set {opt} to {value}"))
def set_setting_given(glimpseproc, server, opt, value):
    """Set a glimpsebrowser setting.

    This is available as "Given:" step so it can be used as "Background:".
    """
    if value == '<empty>':
        value = ''
    value = value.replace('(port)', str(server.port))
    glimpseproc.set_setting(opt, value)


@bdd.given(bdd.parsers.parse("I open {path}"))
def open_path_given(glimpseproc, path):
    """Open a URL.

    This is available as "Given:" step so it can be used as "Background:".

    It always opens a new tab, unlike "When I open ..."
    """
    glimpseproc.open_path(path, new_tab=True)


@bdd.given(bdd.parsers.parse("I run {command}"))
def run_command_given(glimpseproc, command):
    """Run a glimpsebrowser command.

    This is available as "Given:" step so it can be used as "Background:".
    """
    glimpseproc.send_cmd(command)


@bdd.given("I have a fresh instance")
def fresh_instance(glimpseproc):
    """Restart glimpsebrowser instance for tests needing a fresh state."""
    glimpseproc.terminate()
    glimpseproc.start()


@bdd.given("I clean up open tabs")
def clean_open_tabs(glimpseproc):
    """Clean up open windows and tabs."""
    glimpseproc.set_setting('tabs.last_close', 'blank')
    glimpseproc.send_cmd(':window-only')
    glimpseproc.send_cmd(':tab-only --force')
    glimpseproc.send_cmd(':tab-close --force')
    glimpseproc.wait_for_load_finished_url('about:blank')


@bdd.given('pdfjs is available')
def pdfjs_available(data_tmpdir):
    if not pdfjs.is_available():
        pytest.skip("No pdfjs installation found.")


## When


@bdd.when(bdd.parsers.parse("I open {path}"))
def open_path(glimpseproc, server, path):
    """Open a URL.

    - If used like "When I open ... in a new tab", the URL is opened in a new
      tab.
    - With "... in a new window", it's opened in a new window.
    - With "... in a private window" it's opened in a new private window.
    - With "... as a URL", it's opened according to new_instance_open_target.
    """
    path = path.replace('(port)', str(server.port))

    new_tab = False
    new_bg_tab = False
    new_window = False
    private = False
    as_url = False
    wait = True

    new_tab_suffix = ' in a new tab'
    new_bg_tab_suffix = ' in a new background tab'
    new_window_suffix = ' in a new window'
    private_suffix = ' in a private window'
    do_not_wait_suffix = ' without waiting'
    as_url_suffix = ' as a URL'

    while True:
        if path.endswith(new_tab_suffix):
            path = path[:-len(new_tab_suffix)]
            new_tab = True
        elif path.endswith(new_bg_tab_suffix):
            path = path[:-len(new_bg_tab_suffix)]
            new_bg_tab = True
        elif path.endswith(new_window_suffix):
            path = path[:-len(new_window_suffix)]
            new_window = True
        elif path.endswith(private_suffix):
            path = path[:-len(private_suffix)]
            private = True
        elif path.endswith(as_url_suffix):
            path = path[:-len(as_url_suffix)]
            as_url = True
        elif path.endswith(do_not_wait_suffix):
            path = path[:-len(do_not_wait_suffix)]
            wait = False
        else:
            break

    glimpseproc.open_path(path, new_tab=new_tab, new_bg_tab=new_bg_tab,
                       new_window=new_window, private=private, as_url=as_url,
                       wait=wait)


@bdd.when(bdd.parsers.parse("I set {opt} to {value}"))
def set_setting(glimpseproc, server, opt, value):
    """Set a glimpsebrowser setting."""
    if value == '<empty>':
        value = ''
    value = value.replace('(port)', str(server.port))
    glimpseproc.set_setting(opt, value)


@bdd.when(bdd.parsers.parse("I run {command}"))
def run_command(glimpseproc, server, tmpdir, command):
    """Run a glimpsebrowser command.

    The suffix "with count ..." can be used to pass a count to the command.
    """
    if 'with count' in command:
        command, count = command.split(' with count ')
        count = int(count)
    else:
        count = None

    invalid_tag = ' (invalid command)'
    if command.endswith(invalid_tag):
        command = command[:-len(invalid_tag)]
        invalid = True
    else:
        invalid = False

    command = command.replace('(port)', str(server.port))
    command = command.replace('(testdata)', testutils.abs_datapath())
    command = command.replace('(tmpdir)', str(tmpdir))
    command = command.replace('(dirsep)', os.sep)
    command = command.replace('(echo-exe)', _get_echo_exe_path())

    glimpseproc.send_cmd(command, count=count, invalid=invalid)


@bdd.when(bdd.parsers.parse("I reload"))
def reload(qtbot, server, glimpseproc, command):
    """Reload and wait until a new request is received."""
    with qtbot.waitSignal(server.new_request):
        glimpseproc.send_cmd(':reload')


@bdd.when(bdd.parsers.parse("I wait until {path} is loaded"))
def wait_until_loaded(glimpseproc, path):
    """Wait until the given path is loaded (as per glimpsebrowser log)."""
    glimpseproc.wait_for_load_finished(path)


@bdd.when(bdd.parsers.re(r'I wait for (?P<is_regex>regex )?"'
                         r'(?P<pattern>[^"]+)" in the log(?P<do_skip> or skip '
                         r'the test)?'))
def wait_in_log(glimpseproc, is_regex, pattern, do_skip):
    """Wait for a given pattern in the glimpsebrowser log.

    If used like "When I wait for regex ... in the log" the argument is treated
    as regex. Otherwise, it's treated as a pattern (* can be used as wildcard).
    """
    if is_regex:
        pattern = re.compile(pattern)

    line = glimpseproc.wait_for(message=pattern, do_skip=bool(do_skip))
    line.expected = True


@bdd.when(bdd.parsers.re(r'I wait for the (?P<category>error|message|warning) '
                         r'"(?P<message>.*)"'))
def wait_for_message(glimpseproc, server, category, message):
    """Wait for a given statusbar message/error/warning."""
    glimpseproc.log_summary('Waiting for {} "{}"'.format(category, message))
    expect_message(glimpseproc, server, category, message)


@bdd.when(bdd.parsers.parse("I wait {delay}s"))
def wait_time(glimpseproc, delay):
    """Sleep for the given delay."""
    time.sleep(float(delay))


@bdd.when(bdd.parsers.re('I press the keys? "(?P<keys>[^"]*)"'))
def press_keys(glimpseproc, keys):
    """Send the given fake keys to glimpsebrowser."""
    glimpseproc.press_keys(keys)


@bdd.when("selection is supported")
def selection_supported(qapp):
    """Skip the test if selection isn't supported."""
    if not qapp.clipboard().supportsSelection():
        pytest.skip("OS doesn't support primary selection!")


@bdd.when("selection is not supported")
def selection_not_supported(qapp):
    """Skip the test if selection is supported."""
    if qapp.clipboard().supportsSelection():
        pytest.skip("OS supports primary selection!")


@bdd.when(bdd.parsers.re(r'I put "(?P<content>.*)" into the '
                         r'(?P<what>primary selection|clipboard)'))
def fill_clipboard(glimpseproc, server, what, content):
    content = content.replace('(port)', str(server.port))
    content = content.replace(r'\n', '\n')
    glimpseproc.send_cmd(':debug-set-fake-clipboard "{}"'.format(content))


@bdd.when(bdd.parsers.re(r'I put the following lines into the '
                         r'(?P<what>primary selection|clipboard):\n'
                         r'(?P<content>.+)$', flags=re.DOTALL))
def fill_clipboard_multiline(glimpseproc, server, what, content):
    fill_clipboard(glimpseproc, server, what, textwrap.dedent(content))


@bdd.when(bdd.parsers.parse('I hint with args "{args}"'))
def hint(glimpseproc, args):
    glimpseproc.send_cmd(':hint {}'.format(args))
    glimpseproc.wait_for(message='hints: *')


@bdd.when(bdd.parsers.parse('I hint with args "{args}" and follow {letter}'))
def hint_and_follow(glimpseproc, args, letter):
    args = args.replace('(testdata)', testutils.abs_datapath())
    glimpseproc.send_cmd(':hint {}'.format(args))
    glimpseproc.wait_for(message='hints: *')
    glimpseproc.send_cmd(':follow-hint {}'.format(letter))


@bdd.when("I wait until the scroll position changed")
def wait_scroll_position(glimpseproc):
    glimpseproc.wait_scroll_pos_changed()


@bdd.when(bdd.parsers.parse("I wait until the scroll position changed to "
                            "{x}/{y}"))
def wait_scroll_position_arg(glimpseproc, x, y):
    glimpseproc.wait_scroll_pos_changed(x, y)


@bdd.when(bdd.parsers.parse('I wait for the javascript message "{message}"'))
def javascript_message_when(glimpseproc, message):
    """Make sure the given message was logged via javascript."""
    glimpseproc.wait_for_js(message)


@bdd.when("I clear SSL errors")
def clear_ssl_errors(request, glimpseproc):
    if request.config.webengine:
        glimpseproc.terminate()
        glimpseproc.start()
    else:
        glimpseproc.send_cmd(':debug-clear-ssl-errors')


@bdd.when("the documentation is up to date")
def update_documentation():
    """Update the docs before testing :help."""
    base_path = os.path.dirname(os.path.abspath(glimpsebrowser.__file__))
    doc_path = os.path.join(base_path, 'html', 'doc')
    script_path = os.path.join(base_path, '..', 'scripts')

    try:
        os.mkdir(doc_path)
    except FileExistsError:
        pass

    files = os.listdir(doc_path)
    if files and all(docutils.docs_up_to_date(p) for p in files):
        return

    try:
        subprocess.run(['asciidoc'], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except OSError:
        pytest.skip("Docs outdated and asciidoc unavailable!")

    update_script = os.path.join(script_path, 'asciidoc2html.py')
    subprocess.run([sys.executable, update_script])


## Then


@bdd.then(bdd.parsers.parse("{path} should be loaded"))
def path_should_be_loaded(glimpseproc, path):
    """Make sure the given path was loaded according to the log.

    This is usually the better check compared to "should be requested" as the
    page could be loaded from local cache.
    """
    glimpseproc.wait_for_load_finished(path)


@bdd.then(bdd.parsers.parse("{path} should be requested"))
def path_should_be_requested(server, path):
    """Make sure the given path was loaded from the webserver."""
    server.wait_for(verb='GET', path='/' + path)


@bdd.then(bdd.parsers.parse("The requests should be:\n{pages}"))
def list_of_requests(server, pages):
    """Make sure the given requests were done from the webserver."""
    expected_requests = [server.ExpectedRequest('GET', '/' + path.strip())
                         for path in pages.split('\n')]
    actual_requests = server.get_requests()
    assert actual_requests == expected_requests


@bdd.then(bdd.parsers.parse("The unordered requests should be:\n{pages}"))
def list_of_requests_unordered(server, pages):
    """Make sure the given requests were done (in no particular order)."""
    expected_requests = [server.ExpectedRequest('GET', '/' + path.strip())
                         for path in pages.split('\n')]
    actual_requests = server.get_requests()
    # Requests are not hashable, we need to convert to ExpectedRequests
    actual_requests = [server.ExpectedRequest.from_request(req)
                       for req in actual_requests]
    assert (collections.Counter(actual_requests) ==
            collections.Counter(expected_requests))


@bdd.then(bdd.parsers.re(r'the (?P<category>error|message|warning) '
                         r'"(?P<message>.*)" should be shown'))
def expect_message(glimpseproc, server, category, message):
    """Expect the given message in the glimpsebrowser log."""
    category_to_loglevel = {
        'message': logging.INFO,
        'error': logging.ERROR,
        'warning': logging.WARNING,
    }
    message = message.replace('(port)', str(server.port))
    glimpseproc.mark_expected(category='message',
                           loglevel=category_to_loglevel[category],
                           message=message)


@bdd.then(bdd.parsers.re(r'(?P<is_regex>regex )?"(?P<pattern>[^"]+)" should '
                         r'be logged( with level (?P<loglevel>.*))?'))
def should_be_logged(glimpseproc, server, is_regex, pattern, loglevel):
    """Expect the given pattern on regex in the log."""
    if is_regex:
        pattern = re.compile(pattern)
    else:
        pattern = pattern.replace('(port)', str(server.port))

    args = {
        'message': pattern,
    }
    if loglevel:
        args['loglevel'] = getattr(logging, loglevel.upper())

    line = glimpseproc.wait_for(**args)
    line.expected = True


@bdd.then(bdd.parsers.parse('"{pattern}" should not be logged'))
def ensure_not_logged(glimpseproc, pattern):
    """Make sure the given pattern was *not* logged."""
    glimpseproc.ensure_not_logged(message=pattern)


@bdd.then(bdd.parsers.parse('the javascript message "{message}" should be '
                            'logged'))
def javascript_message_logged(glimpseproc, message):
    """Make sure the given message was logged via javascript."""
    glimpseproc.wait_for_js(message)


@bdd.then(bdd.parsers.parse('the javascript message "{message}" should not be '
                            'logged'))
def javascript_message_not_logged(glimpseproc, message):
    """Make sure the given message was *not* logged via javascript."""
    glimpseproc.ensure_not_logged(category='js',
                               message='[*] {}'.format(message))


@bdd.then(bdd.parsers.parse("The session should look like:\n{expected}"))
def compare_session(request, glimpseproc, expected):
    """Compare the current sessions against the given template.

    partial_compare is used, which means only the keys/values listed will be
    compared.
    """
    glimpseproc.compare_session(expected)


@bdd.then("no crash should happen")
def no_crash():
    """Don't do anything.

    This is actually a NOP as a crash is already checked in the log.
    """
    time.sleep(0.5)


@bdd.then(bdd.parsers.parse("the header {header} should be set to {value}"))
def check_header(glimpseproc, header, value):
    """Check if a given header is set correctly.

    This assumes we're on the server header page.
    """
    content = glimpseproc.get_content()
    data = json.loads(content)
    print(data)
    if value == '<unset>':
        assert header not in data['headers']
    else:
        actual = data['headers'][header]
        assert testutils.pattern_match(pattern=value, value=actual)


@bdd.then(bdd.parsers.parse('the page should contain the html "{text}"'))
def check_contents_html(glimpseproc, text):
    """Check the current page's content based on a substring."""
    content = glimpseproc.get_content(plain=False)
    assert text in content


@bdd.then(bdd.parsers.parse('the page should contain the plaintext "{text}"'))
def check_contents_plain(glimpseproc, text):
    """Check the current page's content based on a substring."""
    content = glimpseproc.get_content().strip()
    assert text in content


@bdd.then(bdd.parsers.parse('the page should not contain the plaintext '
                            '"{text}"'))
def check_not_contents_plain(glimpseproc, text):
    """Check the current page's content based on a substring."""
    content = glimpseproc.get_content().strip()
    assert text not in content


@bdd.then(bdd.parsers.parse('the json on the page should be:\n{text}'))
def check_contents_json(glimpseproc, text):
    """Check the current page's content as json."""
    content = glimpseproc.get_content().strip()
    expected = json.loads(text)
    actual = json.loads(content)
    assert actual == expected


@bdd.then(bdd.parsers.parse("the following tabs should be open:\n{tabs}"))
def check_open_tabs(glimpseproc, request, tabs):
    """Check the list of open tabs in the session.

    This is a lightweight alternative for "The session should look like: ...".

    It expects a list of URLs, with an optional "(active)" suffix.
    """
    session = glimpseproc.get_session()
    active_suffix = ' (active)'
    pinned_suffix = ' (pinned)'
    tabs = tabs.splitlines()
    assert len(session['windows']) == 1
    assert len(session['windows'][0]['tabs']) == len(tabs)

    # If we don't have (active) anywhere, don't check it
    has_active = any(active_suffix in line for line in tabs)
    has_pinned = any(pinned_suffix in line for line in tabs)

    for i, line in enumerate(tabs):
        line = line.strip()
        assert line.startswith('- ')
        line = line[2:]  # remove "- " prefix

        active = False
        pinned = False

        while line.endswith(active_suffix) or line.endswith(pinned_suffix):
            if line.endswith(active_suffix):
                # active
                line = line[:-len(active_suffix)]
                active = True
            else:
                # pinned
                line = line[:-len(pinned_suffix)]
                pinned = True

        session_tab = session['windows'][0]['tabs'][i]
        current_page = session_tab['history'][-1]
        assert current_page['url'] == glimpseproc.path_to_url(line)
        if active:
            assert session_tab['active']
        elif has_active:
            assert 'active' not in session_tab

        if pinned:
            assert current_page['pinned']
        elif has_pinned:
            assert not current_page['pinned']


@bdd.then(bdd.parsers.re(r'the (?P<what>primary selection|clipboard) should '
                         r'contain "(?P<content>.*)"'))
def clipboard_contains(glimpseproc, server, what, content):
    expected = content.replace('(port)', str(server.port))
    expected = expected.replace('\\n', '\n')
    expected = expected.replace('(linesep)', os.linesep)
    glimpseproc.wait_for(message='Setting fake {}: {}'.format(
        what, json.dumps(expected)))


@bdd.then(bdd.parsers.parse('the clipboard should contain:\n{content}'))
def clipboard_contains_multiline(glimpseproc, server, content):
    expected = textwrap.dedent(content).replace('(port)', str(server.port))
    glimpseproc.wait_for(message='Setting fake clipboard: {}'.format(
        json.dumps(expected)))


@bdd.then("glimpsebrowser should quit")
def should_quit(qtbot, glimpseproc):
    glimpseproc.wait_for_quit()


def _get_scroll_values(glimpseproc):
    data = glimpseproc.get_session()
    pos = data['windows'][0]['tabs'][0]['history'][-1]['scroll-pos']
    return (pos['x'], pos['y'])


@bdd.then(bdd.parsers.re(r"the page should be scrolled "
                         r"(?P<direction>horizontally|vertically)"))
def check_scrolled(glimpseproc, direction):
    glimpseproc.wait_scroll_pos_changed()
    x, y = _get_scroll_values(glimpseproc)
    if direction == 'horizontally':
        assert x > 0
        assert y == 0
    else:
        assert x == 0
        assert y > 0


@bdd.then("the page should not be scrolled")
def check_not_scrolled(request, glimpseproc):
    x, y = _get_scroll_values(glimpseproc)
    assert x == 0
    assert y == 0


@bdd.then(bdd.parsers.parse("the option {option} should be set to {value}"))
def check_option(glimpseproc, option, value):
    actual_value = glimpseproc.get_setting(option)
    assert actual_value == value


@bdd.then(bdd.parsers.parse("the per-domain option {option} should be set to "
                            "{value} for {pattern}"))
def check_option_per_domain(glimpseproc, option, value, pattern, server):
    pattern = pattern.replace('(port)', str(server.port))
    actual_value = glimpseproc.get_setting(option, pattern=pattern)
    assert actual_value == value
