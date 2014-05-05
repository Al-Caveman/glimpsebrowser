# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Custom useful datatypes.

Module attributes:
    _UNSET: Used as default argument in the constructor so default can be None.
"""

import logging

_UNSET = object()


def enum(*items, **named):
    """Factory for simple enumerations.

    We really don't need more complex things here, so we don't use python3.4's
    enum, because we'd have to backport things to 3.3 and maybe even 3.2.

    Based on: http://stackoverflow.com/a/1695250/2085149

    Args:
        *items: Items to be sequentally enumerated.
        **named: Items to have a given position/number.
    """
    enums = dict(zip(items, range(len(items))), **named)
    return EnumBase('Enum', (), enums)


class EnumBase(type):

    """Metaclass for enums to provide __getitem__ for reverse mapping."""

    def __init__(cls, name, base, fields):
        super().__init__(name, base, fields)
        cls._mapping = dict((v, k) for k, v in fields.items())

    def __getitem__(cls, key):
        return cls._mapping[key]


class NeighborList:

    """A list of items which saves it current position.

    Class attributes:
        Modes: Different modes, see constructor documentation.

    Attributes:
        idx: The current position in the list.
        _items: A list of all items, accessed through item property.
        _mode: The current mode.
    """

    Modes = enum('block', 'wrap', 'exception')

    def __init__(self, items=None, default=_UNSET, mode=Modes.exception):
        """Constructor.

        Args:
            items: The list of items to iterate in.
            _default: The initially selected value.
            _mode: Behaviour when the first/last item is reached.
                   Modes.block: Stay on the selected item
                   Modes.wrap: Wrap around to the other end
                   Modes.exception: Raise an IndexError.
        """
        if items is None:
            self._items = []
        else:
            self._items = list(items)
        self._default = default
        if default is not _UNSET:
            self.idx = self._items.index(default)
        else:
            self.idx = None
        self._mode = mode

    @property
    def items(self):
        """Getter for items, which should not be set."""
        return self._items

    def getitem(self, offset):
        """Get the item with a relative position.

        Args:
            offset: The offset of the current item, relative to the last one.

        Return:
            The new item.

        Raise:
            IndexError if the border of the list is reached and mode is
                       exception.
        """
        logging.debug("{} items, idx {}, offset {}".format(len(self._items),
                                                           self.idx, offset))
        if not self._items:
            raise IndexError("No items found!")
        try:
            if self.idx + offset >= 0:
                new = self._items[self.idx + offset]
            else:
                raise IndexError
        except IndexError:
            if self._mode == self.Modes.block:
                new = self.curitem()
            elif self._mode == self.Modes.wrap:
                self.idx += offset
                self.idx %= len(self.items)
                new = self.curitem()
            elif self._mode == self.Modes.exception:
                raise
        else:
            self.idx += offset
        return new

    def curitem(self):
        """Get the current item in the list."""
        if self.idx is not None:
            return self._items[self.idx]
        else:
            raise IndexError("No current item!")

    def nextitem(self):
        """Get the next item in the list."""
        return self.getitem(1)

    def previtem(self):
        """Get the previous item in the list."""
        return self.getitem(-1)

    def firstitem(self):
        """Get the first item in the list."""
        if not self._items:
            raise IndexError("No items found!")
        self.idx = 0
        return self.curitem()

    def lastitem(self):
        """Get the last item in the list."""
        if not self._items:
            raise IndexError("No items found!")
        self.idx = len(self._items) - 1
        return self.curitem()

    def reset(self):
        """Reset the position to the default."""
        if self._default is _UNSET:
            raise ValueError("No default set!")
        else:
            self.idx = self._items.index(self._default)
            return self.curitem()


class FakeDict:

    """A fake dictionary which always returns the same value.

    Attributes:
        _val: The value to return.
    """

    def __init__(self, val):
        self._val = val

    def __getitem__(self, _key):
        return self._val


class ImmutableDict(dict):

    """Dict where items only can be set once."""

    def __setitem__(self, key, value):
        if key in self:
            raise ValueError("Key {} already has been set.".format(key))
        super().__setitem__(key, value)
