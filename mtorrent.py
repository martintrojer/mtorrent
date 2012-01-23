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

# Main app loop

import mt_torrent_agent as TA
import mt_state_manager as SM
import mt_logger as L
import mt_config as C
import mt_ui as UI
import mt_utils as U

import os
import datetime as DT
import pdb as P

QUIT = 113
PAUSE = 115
REMOVE = 82
UP = 65
DOWN = 66
NEWLINE = 10
TIMEOUT = -1

class MTorrent:
    def __init__(self):
        self.c = C.Config()

        self.lock_file = None
        try:
            os.stat(self.c["lock_file"])
            raise NameError("mtorrent error; Lockfile present, you might have another mtorrent running? If not, delete the '%s' file and restart mtorrent" % self.c["lock_file"])
        except OSError:
            # os.stat() failed, which is good!
            self.lock_file = open(self.c["lock_file"],'w')
            self.l = L.Logger(self.c)
            self.l.start()
            self.ta = TA.TorrentAgent(self.c, self.l)
            self.l.log("Main:starting the TorrentAgent")
            self.ta.start()
            self.l.log("Main:starting the StateManager")
            self.sm = SM.StateManager(self.c, self.ta, self.l)
            self.ui = UI.UI(self.c, self.sm, self.l)

    def __del__(self):
        if self.lock_file != None:
            self.lock_file.close()
            os.remove(self.c["lock_file"])

    def stop(self):
        self.l.log("Main:stopping the StateManager")
        self.sm.stop()
        self.l.log("Main:stopping the TorrentAgent")
        self.ta.stop()
        self.l.log("Main:stopping the LoggerAgent")
        self.l.stop()

    def run(self):
        running = True
        ipt = ""
        ctr = 0

        lts = { "ui" : DT.datetime.now(),
                "html" : DT.datetime.now(),
                "scan" : DT.datetime.now() }

        self.ui.refresh(ctr, ipt)

        while running:
            #only update the screen ever so often
            now = DT.datetime.now()

            if (now - lts["ui"]).seconds > self.c["ui_update_delay"]:
                self.ui.refresh(ctr, ipt)
                lts["ui"] = now
                ctr += 1
    
            if self.c["write_html"] and ((now - lts["html"]).seconds > self.c["html_update_delay"]):
                html = U.export_html(self.c, self.sm.get_state(), self.l)        
                lts["html"] = now
                try:
                    f = open(self.c["html_file"],"w")
                    f.write(html)
                    f.close()
                except:
                    self.l.log("Main:error writing html file " + self.c["html_file"], L.ERR)

            if (now - lts["scan"]).seconds > self.c["scan_update_delay"]:
                lts["scan"] = now
                files = self.sm.get_scan()

                for t in files["torrent"]:
                    self.ta.add_torrent(t)

                for m in files["magnet"]:
                    try:
                        f = open(m, "rb")
                        uri = f.read()
                        f.close()
                        info_hash = m.split(".magnet")[0]
                        self.ta.add_magnet(uri, info_hash)
                    except:
                        self.l.log("Main:error reading from " + m, L.ERR)

            ch = self.ui.getch()
            self.l.log("Main:getch " + str(ch), L.DBG)

            if ipt != "":
                if ch == TIMEOUT:
                    pass
                elif ch == NEWLINE:
                    self.ta.add_magnet(ipt, "")
                    ipt = ""
                else:
                    try:
                        ipt += "%c" % ch
                    except:
                        pass
            elif ch == TIMEOUT:
                pass
            elif ch == PAUSE:
                s = filter(lambda s: s["is_highlighted"], self.sm.get_state())
                if len(s) == 1:
                    self.ta.toggle_pause(s[0]["source"])
            elif ch == QUIT:
                self.l.log("Shutting down...", L.WARN)
                self.ui.refresh(ctr, "")
                running = False
            elif ch == UP:
                self.ta.highlight_up()
            elif ch == DOWN:
                self.ta.highlight_down()
            elif ch == NEWLINE:
                ipt = " "
            elif ch == REMOVE:
                s = filter(lambda s: s["is_highlighted"], self.sm.get_state())
                if len(s) == 1:
                    self.ta.remove_torrent(s[0]["source"])
                    U.remove_file(s[0]["source"], self.l)
        self.stop()

if __name__ == "__main__":
    try:
        mt = MTorrent()
        mt.run()
    except NameError as m:
        print m
