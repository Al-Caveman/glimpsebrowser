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

"""QtWebKit specific glimpse://* handlers and glue code."""

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply, QNetworkAccessManager

from glimpsebrowser.browser import glimpsescheme
from glimpsebrowser.browser.webkit.network import networkreply
from glimpsebrowser.utils import log, qtutils


def handler(request, operation, current_url):
    """Scheme handler for glimpse:// URLs.

    Args:
        request: QNetworkRequest to answer to.
        operation: The HTTP operation being done.
        current_url: The page we're on currently.

    Return:
        A QNetworkReply.
    """
    if operation != QNetworkAccessManager.GetOperation:
        return networkreply.ErrorNetworkReply(
            request, "Unsupported request type",
            QNetworkReply.ContentOperationNotPermittedError)

    url = request.url()

    if ((url.scheme(), url.host(), url.path()) ==
            ('glimpse', 'settings', '/set')):
        if current_url != QUrl('glimpse://settings/'):
            log.webview.warning("Blocking malicious request from {} to {}"
                                .format(current_url.toDisplayString(),
                                        url.toDisplayString()))
            return networkreply.ErrorNetworkReply(
                request, "Invalid glimpse://settings request",
                QNetworkReply.ContentAccessDenied)

    try:
        mimetype, data = glimpsescheme.data_for_url(url)
    except glimpsescheme.Error as e:
        errors = {
            glimpsescheme.NotFoundError:
                QNetworkReply.ContentNotFoundError,
            glimpsescheme.UrlInvalidError:
                QNetworkReply.ContentOperationNotPermittedError,
            glimpsescheme.RequestDeniedError:
                QNetworkReply.ContentAccessDenied,
            glimpsescheme.SchemeOSError:
                QNetworkReply.ContentNotFoundError,
            glimpsescheme.Error:
                QNetworkReply.InternalServerError,
        }
        exctype = type(e)
        log.misc.error("{} while handling glimpse://* URL".format(
            exctype.__name__))
        return networkreply.ErrorNetworkReply(request, str(e), errors[exctype])
    except glimpsescheme.Redirect as e:
        qtutils.ensure_valid(e.url)
        return networkreply.RedirectNetworkReply(e.url)

    return networkreply.FixedDataNetworkReply(request, data, mimetype)
