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

"""Function to return the url completion model for the `open` command."""

import typing

from glimpsebrowser.completion.models import (completionmodel, listcategory,
                                           histcategory)
from glimpsebrowser.utils import log, objreg
from glimpsebrowser.config import config


_URLCOL = 0
_TEXTCOL = 1


def _delete_history(data):
    urlstr = data[_URLCOL]
    log.completion.debug('Deleting history entry {}'.format(urlstr))
    hist = objreg.get('web-history')
    hist.delete_url(urlstr)


def _delete_bookmark(data: typing.Sequence[str]) -> None:
    urlstr = data[_URLCOL]
    log.completion.debug('Deleting bookmark {}'.format(urlstr))
    bookmark_manager = objreg.get('bookmark-manager')
    bookmark_manager.delete(urlstr)


def _delete_quickmark(data: typing.Sequence[str]) -> None:
    name = data[_TEXTCOL]
    quickmark_manager = objreg.get('quickmark-manager')
    log.completion.debug('Deleting quickmark {}'.format(name))
    quickmark_manager.delete(name)


def url(*, info):
    """A model which combines various URLs.

    This combines:
    - bookmarks
    - quickmarks
    - search engines
    - web history URLs

    Used for the `open` command.
    """
    model = completionmodel.CompletionModel(column_widths=(40, 50, 10))

    # pylint: disable=bad-config-option
    quickmarks = [(url, name) for (name, url)
                  in objreg.get('quickmark-manager').marks.items()]
    bookmarks = objreg.get('bookmark-manager').marks.items()
    searchengines = [(k, v) for k, v
                     in sorted(config.val.url.searchengines.items())
                     if k != 'DEFAULT']
    # pylint: enable=bad-config-option
    categories = config.val.completion.open_categories
    models = {}

    if searchengines and 'searchengines' in categories:
        models['searchengines'] = listcategory.ListCategory(
            'Search engines', searchengines, sort=False)

    if quickmarks and 'quickmarks' in categories:
        models['quickmarks'] = listcategory.ListCategory(
            'Quickmarks', quickmarks, delete_func=_delete_quickmark,
            sort=False)
    if bookmarks and 'bookmarks' in categories:
        models['bookmarks'] = listcategory.ListCategory(
            'Bookmarks', bookmarks, delete_func=_delete_bookmark, sort=False)

    history_disabled = info.config.get('completion.web_history.max_items') == 0
    if not history_disabled and 'history' in categories:
        hist_cat = histcategory.HistoryCategory(delete_func=_delete_history)
        models['history'] = hist_cat

    for category in categories:
        if category in models:
            model.add_category(models[category])

    return model
