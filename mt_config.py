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

# Configuration
#export PYTHONPATH=/usr/local/lib/python2.7/site-packages/

import libtorrent as LT
import mt_logger as L

import ConfigParser as CP
import os

MTORRENT_VERSION = "0.3"
SESSION_PATH = "session"
WATCH_PATH = "watch"

default = { "log_level": L.ALL,
            "log_echo": False,    # echo log to STDOUT
            "write_html": False,

            "version": MTORRENT_VERSION,
            "version_long": ".oO mtorrent " + MTORRENT_VERSION + " (libtorrent-rasterbar " + LT.version + ") Oo.",
            "version_short": "mtorrent" + MTORRENT_VERSION + "/lbtorrent" + LT.version,

            #seconds
            "state_update_delay": 2.5,
            "ui_update_delay": 0.5,
            "scan_update_delay": 10,
            "html_update_delay": 15,
            "message_delay": 10,

            "session_path": SESSION_PATH,
            "session_file": SESSION_PATH + "/mtorrent_session",
            "watch_path": WATCH_PATH,
            "html_file": "web/mtorrent_status.html",
            "log_file": "mtorrent.log",
            "lock_file": SESSION_PATH + "/mtorrent_lock",
            
            "save_path": ".",
            "storage_mode": LT.storage_mode_t.storage_mode_sparse,
            "dup_is_error": False,
            "auto_managed": True,
            "max_connections": 50,
            "max_uploads": -1,
            "ratio": 0.0,
            "upload_limit": 0,
            "download_limit": 0,
            "resolve_countries": False,
            "start_as_paused": False,
            
            "auto_upload_slots": True,
            "ann_all_trackers": False,
            "optimize_hash_speed": False,
            "disk_cache_algo": LT.disk_cache_algo_t.largest_contiguous,
            "dht_as_fallback": False,

            "listen_on": (6881, 6891),
            "use_dht" : True,
            "use_upnp": True,
            "dht_router1": ("router.bittorrent.com", 6881),
            "dht_router2": ("router.utorrent.com", 6881),
            "dht_router3": ("router.bitcomet.com", 6881) }

class Config:
    def __init__(self):
        self.c = CP.ConfigParser()
        self.c.read(os.environ["HOME"] + "/.mtorrentrc")

    def __getitem__(self,key):
        try:
            r = self.c.get("mtorrent",key)
            return eval(r)
        except:
            return default[key]

