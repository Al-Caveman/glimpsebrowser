# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014-2019 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>
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

"""Text displayed in the statusbar."""

import enum

from PyQt5.QtCore import pyqtSlot

from glimpsebrowser.mainwindow.statusbar import textbase
from glimpsebrowser.utils import log


class Text(textbase.TextBase):

    """Text displayed in the statusbar.

    Attributes:
        _normaltext: The "permanent" text. Never automatically cleared.
        _temptext: The temporary text to display.

        The temptext is shown from StatusBar when a temporary text or error is
        available. If not, the permanent text is shown.
    """

    Text = enum.Enum('Text', ['normal', 'temp'])

    def __init__(self, parent=None):
        super().__init__(parent)
        self._normaltext = ''
        self._temptext = ''

    def set_text(self, which, text):
        """Set a text.

        Args:
            which: Which text to set, a self.Text instance.
            text: The text to set.
        """
        log.statusbar.debug("Setting {} text to '{}'.".format(
            which.name, text))
        if which is self.Text.normal:
            self._normaltext = text
        elif which is self.Text.temp:
            self._temptext = text
        else:
            raise ValueError("Invalid value {} for which!".format(which))
        self.update_text()

    @pyqtSlot(str)
    def maybe_reset_text(self, text):
        """Clear a normal text if it still matches an expected text."""
        if self._normaltext == text:
            log.statusbar.debug("Resetting: '{}'".format(text))
            self.set_text(self.Text.normal, '')
        else:
            log.statusbar.debug("Ignoring reset: '{}'".format(text))

    def update_text(self):
        """Update QLabel text when needed."""
        if self._temptext:
            self.setText(self._temptext)
        elif self._normaltext:
            self.setText(self._normaltext)
        else:
            self.setText('')
