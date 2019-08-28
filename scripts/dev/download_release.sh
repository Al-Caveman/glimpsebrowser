#!/bin/bash
set -e

# This script downloads the given release from GitHub so we can mirror it on
# glimpsebrowser.org.

tmpdir=$(mktemp -d)
oldpwd=$PWD

if [[ $# != 1 ]]; then
    echo "Usage: $0 <version>" >&2
    exit 1
fi

cd "$tmpdir"
mkdir windows

base="https://github.com/glimpsebrowser/glimpsebrowser/releases/download/v$1"

wget "$base/glimpsebrowser-$1.tar.gz"
wget "$base/glimpsebrowser-$1.tar.gz.asc"
wget "$base/glimpsebrowser-$1.dmg"
wget "$base/glimpsebrowser_${1}-1_all.deb"

cd windows
wget "$base/glimpsebrowser-${1}-amd64.msi"
wget "$base/glimpsebrowser-${1}-win32.msi"
wget "$base/glimpsebrowser-${1}-windows-standalone-amd64.zip"
wget "$base/glimpsebrowser-${1}-windows-standalone-win32.zip"

dest="/srv/http/glimpsebrowser/releases/v$1"
cd "$oldpwd"
sudo mv "$tmpdir" "$dest"
sudo chown -R http:http "$dest"
