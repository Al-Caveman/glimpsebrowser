#!/usr/bin/env python3
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

"""Generate file_version_info.txt for Pyinstaller use with Windows builds."""

import os.path
import sys

# pylint: disable=import-error,no-member,useless-suppression
from PyInstaller.utils.win32 import versioninfo as vs
# pylint: enable=import-error,no-member,useless-suppression

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir,
                                os.pardir))

import glimpsebrowser
from scripts import utils


def main():
    utils.change_cwd()
    out_filename = 'misc/file_version_info.txt'

    filevers = glimpsebrowser.__version_info__ + (0,)
    prodvers = glimpsebrowser.__version_info__ + (0,)
    str_filevers = glimpsebrowser.__version__
    str_prodvers = glimpsebrowser.__version__

    comment_text = glimpsebrowser.__doc__
    copyright_text = glimpsebrowser.__copyright__
    trademark_text = ("glimpsebrowser is free software under the GNU General "
                      "Public License")

    # https://www.science.co.il/language/Locale-codes.php#definitions
    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd317756.aspx
    en_us = 1033  # 0x0409
    utf_16 = 1200  # 0x04B0

    ffi = vs.FixedFileInfo(filevers, prodvers)

    kids = [
        vs.StringFileInfo([
            # 0x0409: MAKELANGID(LANG_ENGLISH, SUBLANG_ENGLISH_US)
            # 0x04B0: codepage 1200 (UTF-16LE)
            vs.StringTable('040904B0', [
                vs.StringStruct('Comments', comment_text),
                vs.StringStruct('CompanyName', "glimpsebrowser.org"),
                vs.StringStruct('FileDescription', "glimpsebrowser"),
                vs.StringStruct('FileVersion', str_filevers),
                vs.StringStruct('InternalName', "glimpsebrowser"),
                vs.StringStruct('LegalCopyright', copyright_text),
                vs.StringStruct('LegalTrademarks', trademark_text),
                vs.StringStruct('OriginalFilename', "glimpsebrowser.exe"),
                vs.StringStruct('ProductName', "glimpsebrowser"),
                vs.StringStruct('ProductVersion', str_prodvers)
            ]),
        ]),
        vs.VarFileInfo([vs.VarStruct('Translation', [en_us, utf_16])]),
    ]

    file_version_info = vs.VSVersionInfo(ffi, kids)

    with open(out_filename, 'w', encoding='utf-8') as f:
        f.write(str(file_version_info))


if __name__ == '__main__':
    main()
