#!/usr/bin/env python3
# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014-2019 Florian Bruhin (The-Compiler) <me@the-compiler.org>

# this file is part of glimpsebrowser.
#
# glimpsebrowser is free software: you can redistribute it and/or modify
# it under the terms of the gnu general public license as published by
# the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# glimpsebrowser is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the
# gnu general public license for more details.
#
# you should have received a copy of the gnu general public license
# along with glimpsebrowser.  if not, see <http://www.gnu.org/licenses/>.

"""Generate Qt resources based on source files."""

import subprocess

with open('glimpsebrowser/resources.py', 'w', encoding='utf-8') as f:
    subprocess.run(['pyrcc5', 'glimpsebrowser.rcc'], stdout=f, check=True)
