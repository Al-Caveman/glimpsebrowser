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

"""Test interceptor.py for webengine."""


import pytest

pytest.importorskip('PyQt5.QtWebEngineWidgets')

from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInfo

from glimpsebrowser.browser.webengine import interceptor


class TestWebengineInterceptor:

    def test_requestinfo_dict_valid(self):
        """Test that the RESOURCE_TYPES dict is not missing any values."""
        qb_keys = interceptor.RequestInterceptor.RESOURCE_TYPES.keys()
        qt_keys = {i for i in vars(QWebEngineUrlRequestInfo).values()
                   if isinstance(i, QWebEngineUrlRequestInfo.ResourceType)}
        assert qt_keys == qb_keys
