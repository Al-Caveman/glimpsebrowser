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

"""QtWebEngine specific glimpse://* handlers and glue code."""

from PyQt5.QtCore import QBuffer, QIODevice, QUrl
from PyQt5.QtWebEngineCore import (QWebEngineUrlSchemeHandler,
                                   QWebEngineUrlRequestJob)
try:
    from PyQt5.QtWebEngineCore import QWebEngineUrlScheme  # type: ignore
except ImportError:
    # Added in Qt 5.12
    QWebEngineUrlScheme = None

from glimpsebrowser.browser import glimpsescheme
from glimpsebrowser.utils import log, qtutils


class GlimpseSchemeHandler(QWebEngineUrlSchemeHandler):

    """Handle glimpse://* requests on QtWebEngine."""

    def install(self, profile):
        """Install the handler for glimpse:// URLs on the given profile."""
        if QWebEngineUrlScheme is not None:
            assert QWebEngineUrlScheme.schemeByName(b'glimpse') is not None

        profile.installUrlSchemeHandler(b'glimpse', self)
        if (qtutils.version_check('5.11', compiled=False) and
                not qtutils.version_check('5.12', compiled=False)):
            # WORKAROUND for https://bugreports.qt.io/browse/QTBUG-63378
            profile.installUrlSchemeHandler(b'chrome-error', self)
            profile.installUrlSchemeHandler(b'chrome-extension', self)

    def _check_initiator(self, job):
        """Check whether the initiator of the job should be allowed.

        Only the browser itself or glimpse:// pages should access any of those
        URLs. The request interceptor further locks down glimpse://settings/set.

        Args:
            job: QWebEngineUrlRequestJob

        Return:
            True if the initiator is allowed, False if it was blocked.
        """
        try:
            initiator = job.initiator()
            request_url = job.requestUrl()
        except AttributeError:
            # Added in Qt 5.11
            return True

        # https://codereview.qt-project.org/#/c/234849/
        is_opaque = initiator == QUrl('null')
        target = request_url.scheme(), request_url.host()

        if is_opaque and not qtutils.version_check('5.12'):
            # WORKAROUND for https://bugreports.qt.io/browse/QTBUG-70421
            # When we don't register the glimpse:// scheme, all requests are
            # flagged as opaque.
            return True

        if (target == ('glimpse', 'testdata') and
                is_opaque and
                qtutils.version_check('5.12')):
            # Allow requests to glimpse://testdata, as this is needed in Qt 5.12
            # for all tests to work properly. No glimpse://testdata handler is
            # installed outside of tests.
            return True

        if initiator.isValid() and initiator.scheme() != 'glimpse':
            log.misc.warning("Blocking malicious request from {} to {}".format(
                initiator.toDisplayString(),
                request_url.toDisplayString()))
            job.fail(QWebEngineUrlRequestJob.RequestDenied)
            return False

        return True

    def requestStarted(self, job):
        """Handle a request for a glimpse: scheme.

        This method must be reimplemented by all custom URL scheme handlers.
        The request is asynchronous and does not need to be handled right away.

        Args:
            job: QWebEngineUrlRequestJob
        """
        url = job.requestUrl()

        if url.scheme() in ['chrome-error', 'chrome-extension']:
            # WORKAROUND for https://bugreports.qt.io/browse/QTBUG-63378
            job.fail(QWebEngineUrlRequestJob.UrlInvalid)
            return

        if not self._check_initiator(job):
            return

        if job.requestMethod() != b'GET':
            job.fail(QWebEngineUrlRequestJob.RequestDenied)
            return

        assert url.scheme() == 'glimpse'

        log.misc.debug("Got request for {}".format(url.toDisplayString()))
        try:
            mimetype, data = glimpsescheme.data_for_url(url)
        except glimpsescheme.Error as e:
            errors = {
                glimpsescheme.NotFoundError:
                    QWebEngineUrlRequestJob.UrlNotFound,
                glimpsescheme.UrlInvalidError:
                    QWebEngineUrlRequestJob.UrlInvalid,
                glimpsescheme.RequestDeniedError:
                    QWebEngineUrlRequestJob.RequestDenied,
                glimpsescheme.SchemeOSError:
                    QWebEngineUrlRequestJob.UrlNotFound,
                glimpsescheme.Error:
                    QWebEngineUrlRequestJob.RequestFailed,
            }
            exctype = type(e)
            log.misc.error("{} while handling glimpse://* URL".format(
                exctype.__name__))
            job.fail(errors[exctype])
        except glimpsescheme.Redirect as e:
            qtutils.ensure_valid(e.url)
            job.redirect(e.url)
        else:
            log.misc.debug("Returning {} data".format(mimetype))

            # We can't just use the QBuffer constructor taking a QByteArray,
            # because that somehow segfaults...
            # https://www.riverbankcomputing.com/pipermail/pyqt/2016-September/038075.html
            buf = QBuffer(parent=self)
            buf.open(QIODevice.WriteOnly)
            buf.write(data)
            buf.seek(0)
            buf.close()
            job.reply(mimetype.encode('ascii'), buf)


def init():
    """Register the glimpse:// scheme.

    Note this needs to be called early, before constructing any QtWebEngine
    classes.
    """
    if QWebEngineUrlScheme is not None:
        assert not QWebEngineUrlScheme.schemeByName(b'glimpse').name()
        scheme = QWebEngineUrlScheme(b'glimpse')
        scheme.setFlags(QWebEngineUrlScheme.LocalScheme |
                        QWebEngineUrlScheme.LocalAccessAllowed)
        QWebEngineUrlScheme.registerScheme(scheme)
