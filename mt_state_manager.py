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

# Class that maintains the torrent states data for the UI
# .. and the scan data of the watch folder

import mt_logger as L
import mt_utils as U

import threading as T

class StateManager():
    def __init__(self, config, torrent_agent, logger):
        self.c = config
        self.ta = torrent_agent
        self.l = logger
        self.state = {}
        self.scan = {"torrent": [], "magnet": []}
        self.exclude = set()
        self.running = True
        # We can get away with a lock here, the only one in the program!
        self.lock = T.Lock()
        self.__start_state_timer()
        self.__start_scan_timer()

    def __del__(self):
        try:
            self.state_timer.cancel()
            self.scan_timer.cancel()
            self.lock.release()
        except:
            pass

    def __start_state_timer(self):
        if self.running:
            self.state_timer = T.Timer(self.c["state_update_delay"], self.__update_state)
            self.state_timer.start()

    def __start_scan_timer(self):
        if self.running:
            self.scan_timer = T.Timer(self.c["scan_update_delay"], self.__update_scan)
            self.scan_timer.start()

    def __update_state(self):
        if self.running:
            self.l.log("StateManager:requesting the state", L.DBG)
            res = self.ta.get_state()

            self.lock.acquire(True)
            self.state = res
            self.lock.release()        

            self.__start_state_timer()

    def __update_scan(self):
        if self.running:
            self.exclude = set()
            files = {"torrent":[], "magnet": []}
            try:
                self.l.log("StateManager:scan_dir " + self.c["watch_path"], L.DBG)
                files = U.scan_dir(self.c["watch_path"])
            except:
                self.l.log("StateManager:failed to scan dir " + self.c["watch_path"], L.WARN)

            self.lock.acquire(True)
            self.scan = files
            self.lock.release()        

            self.__start_scan_timer()
            
    def get_state(self):
        self.lock.acquire(True)
        res = self.state
        self.lock.release()

        return res

    def get_scan(self):
        self.lock.acquire(True)
        res = self.scan
        self.lock.release()

        return {"torrent": set(res["torrent"]) - self.exclude, 
                "magnet": set(res["magnet"]) - self.exclude}

    def remove_file(self, name):
        self.lock.acquire(True)
        self.exclude.add(name)
        self.lock.release()

    def stop(self):
        self.running = False

