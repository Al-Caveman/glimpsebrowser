#!/usr/bin/env python3
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

"""Build a new release."""


import os
import os.path
import sys
import time
import shutil
import plistlib
import subprocess
import argparse
import tarfile
import tempfile
import collections
import re

try:
    import winreg
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir,
                                os.pardir))

import glimpsebrowser
from scripts import utils
from scripts.dev import update_3rdparty


def call_script(name, *args, python=sys.executable):
    """Call a given shell script.

    Args:
        name: The script to call.
        *args: The arguments to pass.
        python: The python interpreter to use.
    """
    path = os.path.join(os.path.dirname(__file__), os.pardir, name)
    subprocess.run([python, path] + list(args), check=True)


def call_tox(toxenv, *args, python=sys.executable):
    """Call tox.

    Args:
        toxenv: Which tox environment to use
        *args: The arguments to pass.
        python: The python interpreter to use.
    """
    env = os.environ.copy()
    env['PYTHON'] = python
    env['PATH'] = os.environ['PATH'] + os.pathsep + os.path.dirname(python)
    subprocess.run(
        [sys.executable, '-m', 'tox', '-vv', '-e', toxenv] + list(args),
        env=env, check=True)


def run_asciidoc2html(args):
    """Common buildsteps used for all OS'."""
    utils.print_title("Running asciidoc2html.py")
    if args.asciidoc is not None:
        a2h_args = ['--asciidoc'] + args.asciidoc
    else:
        a2h_args = []
    call_script('asciidoc2html.py', *a2h_args)


def _maybe_remove(path):
    """Remove a path if it exists."""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def _filter_whitelisted(output, patterns):
    for line in output.decode('utf-8').splitlines():
        if not any(re.fullmatch(pattern, line) for pattern in patterns):
            yield line


def smoke_test(executable):
    """Try starting the given glimpsebrowser executable."""
    stdout_whitelist = []
    stderr_whitelist = [
        # PyInstaller debug output
        r'\[.*\] PyInstaller Bootloader .*',
        r'\[.*\] LOADER: .*',

        # https://github.com/glimpsebrowser/glimpsebrowser/issues/4919
        (r'objc\[.*\]: .* One of the two will be used\. '
         r'Which one is undefined\.'),
        (r'QCoreApplication::applicationDirPath: Please instantiate the '
         r'QApplication object first'),
    ]

    proc = subprocess.run([executable, '--no-err-windows', '--nowindow',
                           '--temp-basedir', 'about:blank',
                           ':later 500 quit'], check=True, capture_output=True)
    stdout = '\n'.join(_filter_whitelisted(proc.stdout, stdout_whitelist))
    stderr = '\n'.join(_filter_whitelisted(proc.stderr, stderr_whitelist))
    if stdout:
        raise Exception("Unexpected stdout:\n{}".format(stdout))
    if stderr:
        raise Exception("Unexpected stderr:\n{}".format(stderr))


def patch_mac_app():
    """Patch .app to use our Info.plist and save some space."""
    app_path = os.path.join('dist', 'glimpsebrowser.app')

    # Patch Info.plist - pyinstaller's options are too limiting
    plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
    with open(plist_path, "rb") as f:
        plist_data = plistlib.load(f)
    plist_data.update(INFO_PLIST_UPDATES)
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)

    # Replace some duplicate files by symlinks
    framework_path = os.path.join(app_path, 'Contents', 'MacOS', 'PyQt5',
                                  'Qt', 'lib', 'QtWebEngineCore.framework')

    core_lib = os.path.join(framework_path, 'Versions', '5', 'QtWebEngineCore')
    os.remove(core_lib)
    core_target = os.path.join(*[os.pardir] * 7, 'MacOS', 'QtWebEngineCore')
    os.symlink(core_target, core_lib)

    framework_resource_path = os.path.join(framework_path, 'Resources')
    for name in os.listdir(framework_resource_path):
        file_path = os.path.join(framework_resource_path, name)
        target = os.path.join(*[os.pardir] * 5, name)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        os.symlink(target, file_path)


INFO_PLIST_UPDATES = {
    'CFBundleVersion': glimpsebrowser.__version__,
    'CFBundleShortVersionString': glimpsebrowser.__version__,
    'NSSupportsAutomaticGraphicsSwitching': True,
    'NSHighResolutionCapable': True,
    'CFBundleURLTypes': [{
        "CFBundleURLName": "http(s) URL",
        "CFBundleURLSchemes": ["http", "https"]
    }, {
        "CFBundleURLName": "local file URL",
        "CFBundleURLSchemes": ["file"]
    }],
    'CFBundleDocumentTypes': [{
        "CFBundleTypeExtensions": ["html", "htm"],
        "CFBundleTypeMIMETypes": ["text/html"],
        "CFBundleTypeName": "HTML document",
        "CFBundleTypeOSTypes": ["HTML"],
        "CFBundleTypeRole": "Viewer",
    }, {
        "CFBundleTypeExtensions": ["xhtml"],
        "CFBundleTypeMIMETypes": ["text/xhtml"],
        "CFBundleTypeName": "XHTML document",
        "CFBundleTypeRole": "Viewer",
    }]
}


def build_mac():
    """Build macOS .dmg/.app."""
    utils.print_title("Cleaning up...")
    for f in ['wc.dmg', 'template.dmg']:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass
    for d in ['dist', 'build']:
        shutil.rmtree(d, ignore_errors=True)
    utils.print_title("Updating 3rdparty content")
    update_3rdparty.run(ace=False, pdfjs=True, fancy_dmg=False)
    utils.print_title("Building .app via pyinstaller")
    call_tox('pyinstaller', '-r')
    utils.print_title("Patching .app")
    patch_mac_app()
    utils.print_title("Building .dmg")
    subprocess.run(['make', '-f', 'scripts/dev/Makefile-dmg'], check=True)

    dmg_name = 'glimpsebrowser-{}.dmg'.format(glimpsebrowser.__version__)
    os.rename('glimpsebrowser.dmg', dmg_name)

    utils.print_title("Running smoke test")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(['hdiutil', 'attach', dmg_name,
                            '-mountpoint', tmpdir], check=True)
            try:
                binary = os.path.join(tmpdir, 'glimpsebrowser.app', 'Contents',
                                      'MacOS', 'glimpsebrowser')
                smoke_test(binary)
            finally:
                time.sleep(5)
                subprocess.run(['hdiutil', 'detach', tmpdir])
    except PermissionError as e:
        print("Failed to remove tempdir: {}".format(e))

    return [(dmg_name, 'application/x-apple-diskimage', 'macOS .dmg')]


def patch_windows(out_dir, x64):
    """Copy missing DLLs for windows into the given output."""
    dll_dir = os.path.join('.tox', 'pyinstaller', 'lib', 'site-packages',
                           'PyQt5', 'Qt', 'bin')
    # https://github.com/pyinstaller/pyinstaller/issues/4322
    dlls = ['libEGL.dll', 'd3dcompiler_47.dll']
    # https://github.com/pyinstaller/pyinstaller/issues/4321
    if x64:
        dlls += ['libssl-1_1-x64.dll', 'libcrypto-1_1-x64.dll']

    for dll in dlls:
        shutil.copy(os.path.join(dll_dir, dll), out_dir)


def _get_windows_python_path(x64):
    """Get the path to Python.exe on Windows."""
    parts = str(sys.version_info.major), str(sys.version_info.minor)
    ver = ''.join(parts)
    dot_ver = '.'.join(parts)

    if x64:
        path = (r'SOFTWARE\Python\PythonCore\{}\InstallPath'
                .format(dot_ver))
        fallback = r'C:\Python{}\python.exe'.format(ver)
    else:
        path = (r'SOFTWARE\WOW6432Node\Python\PythonCore\{}-32\InstallPath'
                .format(dot_ver))
        fallback = r'C:\Python{}-32\python.exe'.format(ver)

    try:
        key = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, path)
        return winreg.QueryValueEx(key, 'ExecutablePath')[0]
    except FileNotFoundError:
        return fallback


def build_windows():
    """Build windows executables/setups."""
    utils.print_title("Updating 3rdparty content")
    update_3rdparty.run(nsis=True, ace=False, pdfjs=True, fancy_dmg=False)

    utils.print_title("Building Windows binaries")

    python_x64 = _get_windows_python_path(x64=True)
    python_x86 = _get_windows_python_path(x64=False)

    out_pyinstaller = os.path.join('dist', 'glimpsebrowser')
    out_32 = os.path.join('dist',
                          'glimpsebrowser-{}-x86'.format(glimpsebrowser.__version__))
    out_64 = os.path.join('dist',
                          'glimpsebrowser-{}-x64'.format(glimpsebrowser.__version__))

    artifacts = []

    from scripts.dev import gen_versioninfo
    utils.print_title("Updating VersionInfo file")
    gen_versioninfo.main()

    utils.print_title("Running pyinstaller 32bit")
    _maybe_remove(out_32)
    call_tox('pyinstaller', '-r', python=python_x86)
    shutil.move(out_pyinstaller, out_32)
    patch_windows(out_32, x64=False)

    utils.print_title("Running pyinstaller 64bit")
    _maybe_remove(out_64)
    call_tox('pyinstaller', '-r', python=python_x64)
    shutil.move(out_pyinstaller, out_64)
    patch_windows(out_64, x64=True)

    utils.print_title("Running 32bit smoke test")
    smoke_test(os.path.join(out_32, 'glimpsebrowser.exe'))
    utils.print_title("Running 64bit smoke test")
    smoke_test(os.path.join(out_64, 'glimpsebrowser.exe'))

    utils.print_title("Building installers")
    subprocess.run(['makensis.exe',
                    '/DVERSION={}'.format(glimpsebrowser.__version__),
                    'misc/nsis/glimpsebrowser.nsi'], check=True)
    subprocess.run(['makensis.exe',
                    '/DX86',
                    '/DVERSION={}'.format(glimpsebrowser.__version__),
                    'misc/nsis/glimpsebrowser.nsi'], check=True)

    name_32 = 'glimpsebrowser-{}-win32.exe'.format(glimpsebrowser.__version__)
    name_64 = 'glimpsebrowser-{}-amd64.exe'.format(glimpsebrowser.__version__)

    artifacts += [
        (os.path.join('dist', name_32),
         'application/vnd.microsoft.portable-executable',
         'Windows 32bit installer'),
        (os.path.join('dist', name_64),
         'application/vnd.microsoft.portable-executable',
         'Windows 64bit installer'),
    ]

    utils.print_title("Zipping 32bit standalone...")
    name = 'glimpsebrowser-{}-windows-standalone-win32'.format(
        glimpsebrowser.__version__)
    shutil.make_archive(name, 'zip', 'dist', os.path.basename(out_32))
    artifacts.append(('{}.zip'.format(name),
                      'application/zip',
                      'Windows 32bit standalone'))

    utils.print_title("Zipping 64bit standalone...")
    name = 'glimpsebrowser-{}-windows-standalone-amd64'.format(
        glimpsebrowser.__version__)
    shutil.make_archive(name, 'zip', 'dist', os.path.basename(out_64))
    artifacts.append(('{}.zip'.format(name),
                      'application/zip',
                      'Windows 64bit standalone'))

    return artifacts


def build_sdist():
    """Build an sdist and list the contents."""
    utils.print_title("Building sdist")

    _maybe_remove('dist')

    subprocess.run([sys.executable, 'setup.py', 'sdist'], check=True)
    dist_files = os.listdir(os.path.abspath('dist'))
    assert len(dist_files) == 1

    dist_file = os.path.join('dist', dist_files[0])
    subprocess.run(['gpg', '--detach-sign', '-a', dist_file], check=True)

    tar = tarfile.open(dist_file)
    by_ext = collections.defaultdict(list)

    for tarinfo in tar.getmembers():
        if not tarinfo.isfile():
            continue
        name = os.sep.join(tarinfo.name.split(os.sep)[1:])
        _base, ext = os.path.splitext(name)
        by_ext[ext].append(name)

    assert '.pyc' not in by_ext

    utils.print_title("sdist contents")

    for ext, files in sorted(by_ext.items()):
        utils.print_subtitle(ext)
        print('\n'.join(files))

    filename = 'glimpsebrowser-{}.tar.gz'.format(glimpsebrowser.__version__)
    artifacts = [
        (os.path.join('dist', filename), 'application/gzip', 'Source release'),
        (os.path.join('dist', filename + '.asc'), 'application/pgp-signature',
         'Source release - PGP signature'),
    ]

    return artifacts


def test_makefile():
    """Make sure the Makefile works correctly."""
    utils.print_title("Testing makefile")
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(['make', '-f', 'misc/Makefile',
                        'DESTDIR={}'.format(tmpdir), 'install'], check=True)


def read_github_token():
    """Read the GitHub API token from disk."""
    token_file = os.path.join(os.path.expanduser('~'), '.gh_token')
    with open(token_file, encoding='ascii') as f:
        token = f.read().strip()
    return token


def github_upload(artifacts, tag):
    """Upload the given artifacts to GitHub.

    Args:
        artifacts: A list of (filename, mimetype, description) tuples
        tag: The name of the release tag
    """
    import github3
    utils.print_title("Uploading to github...")

    token = read_github_token()
    gh = github3.login(token=token)
    repo = gh.repository('glimpsebrowser', 'glimpsebrowser')

    release = None  # to satisfy pylint
    for release in repo.releases():
        if release.tag_name == tag:
            break
    else:
        raise Exception("No release found for {!r}!".format(tag))

    for filename, mimetype, description in artifacts:
        with open(filename, 'rb') as f:
            basename = os.path.basename(filename)
            asset = release.upload_asset(mimetype, basename, f)
        asset.edit(basename, description)


def pypi_upload(artifacts):
    """Upload the given artifacts to PyPI using twine."""
    utils.print_title("Uploading to PyPI...")
    filenames = [a[0] for a in artifacts]
    subprocess.run([sys.executable, '-m', 'twine', 'upload'] + filenames,
                   check=True)


def upgrade_sdist_dependencies():
    """Make sure we have the latest tools for an sdist release."""
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'twine',
                    'pip', 'wheel', 'setuptools'], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-asciidoc', action='store_true',
                        help="Don't generate docs")
    parser.add_argument('--asciidoc', help="Full path to python and "
                        "asciidoc.py. If not given, it's searched in PATH.",
                        nargs=2, required=False,
                        metavar=('PYTHON', 'ASCIIDOC'))
    parser.add_argument('--upload', action='store_true', required=False,
                        help="Toggle to upload the release to GitHub")
    args = parser.parse_args()
    utils.change_cwd()

    upload_to_pypi = False

    if args.upload:
        # Fail early when trying to upload without github3 installed
        # or without API token
        import github3  # pylint: disable=unused-import
        read_github_token()

    if args.no_asciidoc:
        os.makedirs(os.path.join('glimpsebrowser', 'html', 'doc'), exist_ok=True)
    else:
        run_asciidoc2html(args)

    if os.name == 'nt':
        artifacts = build_windows()
    elif sys.platform == 'darwin':
        artifacts = build_mac()
    else:
        upgrade_sdist_dependencies()
        test_makefile()
        artifacts = build_sdist()
        upload_to_pypi = True

    if args.upload:
        utils.print_title("Press enter to release...")
        input()

        version_tag = "v" + glimpsebrowser.__version__

        github_upload(artifacts, version_tag)
        if upload_to_pypi:
            pypi_upload(artifacts)
    else:
        print()
        utils.print_title("Artifacts")
        for artifact in artifacts:
            print(artifact)


if __name__ == '__main__':
    main()
