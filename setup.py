# mtorrent
# Copyright (c) 2012 Martin Trojer <martin.trojer@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import mt_config as C

from distutils.core import setup

setup(name="mtorrent",
      version=C.MTORRENT_VERSION,
      description="curses torrent client using libtorrent-rasterbar",
      author="Martin Trojer",
      url="https://github.com/martintrojer/mtorrent",
      license="GPLv3",
      py_modules=["mtorrent",
                  "mt_config",
                  "mt_ui",
                  "mt_torrent_agent",
                  "mt_state_manager",
                  "mt_logger", 
                  "mt_utils"],
      scripts=["mtorrent"],
      requires=["libtorrent (>=0.5)"]
)
      
