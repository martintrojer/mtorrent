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
PAUSE_ALL = 83
REMOVE = 114
REMOVE_ALL = 82
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

        lts = { "ui" : DT.datetime.now() - DT.timedelta(seconds = 1),
                "html" : DT.datetime.now() - DT.timedelta(seconds = 2),
                "scan" : DT.datetime.now() - DT.timedelta(seconds = 3)}

        self.ui.refresh(ctr, ipt)
        self.l.log_ui("Welcome!")

        while running:
            #only update the screen ever so often
            now = DT.datetime.now()
            
            if (lts["ui"] < now - DT.timedelta(seconds = self.c["ui_update_delay"])):
                self.ui.refresh(ctr, ipt)
                lts["ui"] = now
                ctr += 1
    
            if self.c["write_html"] and (lts["html"] < now - DT.timedelta(seconds = self.c["html_update_delay"])):
                html = U.export_html(self.c, self.sm.get_state(), self.l)        
                lts["html"] = now
                try:
                    f = open(self.c["html_file"],"w")
                    f.write(html)
                    f.close()
                except:
                    self.l.log("Main:error writing html file " + self.c["html_file"], L.ERR)

            if (lts["scan"] < now - DT.timedelta(seconds = self.c["scan_update_delay"])):
                lts["scan"] = now
                self.ta.scan_and_add(self.c["watch_path"])

            ch = self.ui.getch()
            self.l.log("Main:getch " + str(ch), L.DBG)
#            if ch != -1:
#                self.l.log("getch " + str(ch), L.WARN)

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
                self.ta.toggle_highlighted()
            elif ch == PAUSE_ALL:
                self.ta.toggle_all()
            elif ch == QUIT:
                self.l.log_ui("Shutting down...")
                self.ui.refresh(ctr, "")
                running = False
            elif ch == UP:
                self.ta.highlight_up()
            elif ch == DOWN:
                self.ta.highlight_down()
            elif ch == NEWLINE:
                ipt = " "
            elif ch == REMOVE:
                name = self.ta.remove_highlighted()
                if name != None:
                    self.l.log_ui("Removed file " + name)
            elif ch == REMOVE_ALL:
                for n in self.ta.remove_all():
                    self.l.log_ui("Removed file " + n)

        self.stop()

if __name__ == "__main__":
    try:
        mt = MTorrent()
        mt.run()
    except NameError as m:
        print m
