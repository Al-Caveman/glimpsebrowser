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

import pytest_bdd as bdd
bdd.scenarios('javascript.feature')


@bdd.then("the window sizes should be the same")
def check_window_sizes(glimpseproc):
    hidden = glimpseproc.wait_for_js('hidden window size: *')
    glimpseproc.send_cmd(':jseval --world main updateText("visible")')
    visible = glimpseproc.wait_for_js('visible window size: *')
    hidden_size = hidden.message.split()[-1]
    visible_size = visible.message.split()[-1]
    assert hidden_size == visible_size


test_gm_script = r"""
// ==UserScript==
// @name glimpsebrowser test userscript
// @namespace invalid.org
// @include http://localhost:*/data/hints/iframe.html
// @include http://localhost:*/data/hints/html/wrapped.html
// @exclude ???
// @run-at {stage}
// {frames}
// ==/UserScript==
console.log("Script is running on " + window.location.pathname);
"""


@bdd.when(bdd.parsers.parse("I have a GreaseMonkey file saved for {stage} "
                            "with noframes {frameset}"))
def create_greasemonkey_file(glimpseproc, stage, frameset):
    script_path = os.path.join(glimpseproc.basedir, 'data', 'greasemonkey')
    try:
        os.mkdir(script_path)
    except FileExistsError:
        pass
    file_path = os.path.join(script_path, 'test.user.js')
    if frameset == "set":
        frames = "@noframes"
    elif frameset == "unset":
        frames = ""
    else:
        raise ValueError("noframes can only be set or unset, "
                         "not {}".format(frameset))
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(test_gm_script.format(stage=stage,
                                      frames=frames))
