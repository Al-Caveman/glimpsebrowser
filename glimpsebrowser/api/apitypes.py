# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2018-2019 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>
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

"""A single tab."""

# pylint: disable=unused-import
from glimpsebrowser.browser.browsertab import WebTabError, AbstractTab as Tab
from glimpsebrowser.browser.webelem import (Error as WebElemError,
                                         AbstractWebElement as WebElement)
from glimpsebrowser.utils.usertypes import ClickTarget, JsWorld
from glimpsebrowser.extensions.loader import InitContext
