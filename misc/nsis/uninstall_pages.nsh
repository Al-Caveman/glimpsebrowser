# Copyright 2018 Florian Bruhin (The Compiler) <mail@glimpsebrowser.org>
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

# NSIS pages header. Uses NsisMultiUser plugin and contains portions of
# its demo code, copyright 2017 Richard Drizin, Alex Mitev.


; Pages
!define MUI_UNABORTWARNING ; Show a confirmation when cancelling the installation

!define MULTIUSER_INSTALLMODE_CHANGE_MODE_FUNCTION un.PageInstallModeChangeMode
!insertmacro MULTIUSER_UNPAGE_INSTALLMODE

!define MUI_PAGE_CUSTOMFUNCTION_PRE un.PageComponentsPre
!define MUI_PAGE_CUSTOMFUNCTION_SHOW un.PageComponentsShow
!insertmacro MUI_UNPAGE_COMPONENTS

!insertmacro MUI_UNPAGE_INSTFILES
