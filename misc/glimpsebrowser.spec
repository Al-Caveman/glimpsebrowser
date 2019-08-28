# -*- mode: python -*-

import sys
import os

sys.path.insert(0, os.getcwd())
from scripts import setupcommon

from glimpsebrowser.extensions import loader

block_cipher = None


def get_data_files():
    data_files = [
        ('../glimpsebrowser/html', 'html'),
        ('../glimpsebrowser/img', 'img'),
        ('../glimpsebrowser/javascript', 'javascript'),
        ('../glimpsebrowser/html/doc', 'html/doc'),
        ('../glimpsebrowser/git-commit-id', '.'),
        ('../glimpsebrowser/config/configdata.yml', 'config'),
    ]

    if os.path.exists(os.path.join('glimpsebrowser', '3rdparty', 'pdfjs')):
        data_files.append(('../glimpsebrowser/3rdparty/pdfjs', '3rdparty/pdfjs'))
    else:
        print("Warning: excluding pdfjs as it's not present!")

    return data_files


def get_hidden_imports():
    imports = ['PyQt5.QtOpenGL', 'PyQt5._QOpenGLFunctions_2_0']
    for info in loader.walk_components():
        imports.append(info.name)
    return imports


setupcommon.write_git_file()


if os.name == 'nt':
    icon = '../icons/glimpsebrowser.ico'
elif sys.platform == 'darwin':
    icon = '../icons/glimpsebrowser.icns'
else:
    icon = None


a = Analysis(['../glimpsebrowser/__main__.py'],
             pathex=['misc'],
             binaries=None,
             datas=get_data_files(),
             hiddenimports=get_hidden_imports(),
             hookspath=[],
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='glimpsebrowser',
          icon=icon,
          debug=False,
          strip=False,
          upx=False,
          console=False,
          version='../misc/file_version_info.txt')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='glimpsebrowser')

app = BUNDLE(coll,
             name='glimpsebrowser.app',
             icon=icon,
             # https://github.com/pyinstaller/pyinstaller/blob/b78bfe530cdc2904f65ce098bdf2de08c9037abb/PyInstaller/hooks/hook-PyQt5.QtWebEngineWidgets.py#L24
             bundle_identifier='org.qt-project.Qt.QtWebEngineCore')
