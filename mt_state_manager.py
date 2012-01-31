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

import mt_logger as L
import mt_utils as U

import threading as T

class StateManager():
    def __init__(self, config, torrent_agent, logger):
        self.c = config
        self.ta = torrent_agent
        self.l = logger
        self.state = {}
        self.running = True
        # We can get away with a lock here, the only one in the program!
        self.lock = T.Lock()
        self.__start_state_timer()

    def __del__(self):
        try:
            self.state_timer.cancel()
            self.lock.release()
        except:
            pass

    def __start_state_timer(self):
        if self.running:
            self.state_timer = T.Timer(self.c["state_update_delay"], self.__update_state)
            self.state_timer.start()

    def __update_state(self):
        if self.running:
            self.l.log("StateManager:requesting the state", L.DBG)
            res = self.ta.get_state()

            self.lock.acquire(True)
            self.state = res
            self.lock.release()        

            self.__start_state_timer()

    def get_state(self):
        self.lock.acquire(True)
        res = self.state
        self.lock.release()

        return res

    def stop(self):
        self.running = False

