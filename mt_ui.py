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

# Render the curses UI

import mt_logger as L
import mt_utils as U

import curses as CUR
import datetime as DT

class UI():
    def __init__(self, config, sm, logger): 
        self.c = config
        self.l = logger
        self.l.log("UI:starting (changing terminal mode)", L.DBG)
        self.w = CUR.initscr()
        self.sm = sm
        self.scr_st = {}
        CUR.noecho()
        CUR.cbreak()
        self.w.timeout(int(1000 * self.c["ui_update_delay"]))

        self.endwin = CUR.endwin
        self.dbg = L.DBG

    def __del__(self):
        self.l.log("UI:exiting", self.dbg)
        self.endwin()

    def print_str(self, s, y, x):
        try:
            self.w.addstr(y, x, s)
        except:
            self.l.log("UI:failed to add string to screen")

    def print_str_r(self, s, y, x):
        self.print_str(s, y, x)
        self.w.refresh()

    def print_with_tag(self, s, tag, line):
        try:
            # move might fail if outside the window
            self.w.move(line, 0)
            self.w.clrtoeol()
            self.print_str(tag, line, 0)
            self.print_str(s, line, len(tag))
        except:
            pass

    def print_message(self, s, level, line):
        if level == L.WARN:
            self.print_with_tag(s, "WARNING> ", line)
        elif level == L.ERR:
            self.print_with_tag(s, "ERROR> ", line)
        else:
            self.print_with_tag(s, "$ ", line)
            
    def getch(self):
        return self.w.getch()

    def refresh(self, ctr, ipt):
        factors = [0.34, 0.01, 0.12, 0.12, 0.08, 0.09, 0.09, 0.09]
        x = self.w.getmaxyx()[1]
        y = self.w.getmaxyx()[0]
        self.l.log("UI:maxyx " + str(y) + ":" + str(x), L.DBG)
        
        ss = map(lambda f: int(f * x), factors)
        
        head_fmt = "%c-%ds %c-%ds %c-%ds %c-%ds %c-%ds %c-%ds %c-%ds %c-%ds" % ('%',ss[0],'%',ss[1],'%',ss[2],'%',ss[3],'%',ss[4],'%',ss[5],'%',ss[6],'%',ss[7])
        self.l.log("UI:head_fmt " + head_fmt, L.DBG)

        data_fmt = "%c-%d%c%ds %cd %c-%d%c%ds %c-%d%c%ds %c-%d%c2f %c-%d%c%ds %c-%d%c%ds %c-%d%c%ds" % ('%',ss[0],'.',ss[0],'%','%',ss[2],'.',ss[2],'%',ss[3],'.',ss[3],'%',ss[4],'.','%',ss[5],'.',ss[5],'%',ss[6],'.',ss[6],'%',ss[7],'.',ss[7])
        self.l.log("UI:data_fmt " + data_fmt, L.DBG)

        self.w.clear()
        self.print_str(self.c["version_long"], 0, (x-len(self.c["version_long"]))/2)
        self.w.attron(CUR.A_BOLD)
        self.print_str(head_fmt % ("Name", "A", "Status", "Size", "Done", "Seeds", "Peers", "Down"),1,0)
        self.w.attroff(CUR.A_BOLD)

        i = 0
        for s in self.sm.get_state():
            self.l.log("UI:printing " + str(s), L.DBG)

            if s["is_highlighted"]: self.w.attron(CUR.A_REVERSE)

            hsh = s["hash"]
            if not self.scr_st.has_key(hsh):
                self.scr_st[hsh] = [False for x in range(6)]

            seed_str = "%d(%d)" % (s["seeds"], s["seeds_total"])
            peer_str = "%d(%d)" % (s["peers"], s["peers_total"])
            size_str = U.readable_size(s["size"])
            speed_str = U.readable_size(s["down_rate"])

            scr_st = self.scr_st[hsh]
            name_str, self.scr_st[hsh][0] = U.chop_string(s["name"], ss[0], ctr, scr_st[0])
            state_str, self.scr_st[hsh][1] = U.chop_string(s["status"], ss[2], ctr, scr_st[1])
            size_str, self.scr_st[hsh][2] = U.chop_string(size_str, ss[3], ctr, scr_st[2])
            seed_str, self.scr_st[hsh][3] = U.chop_string(seed_str, ss[5], ctr, scr_st[3])
            peer_str, self.scr_st[hsh][4] = U.chop_string(peer_str, ss[6], ctr, scr_st[4])
            speed_str, self.scr_st[hsh][5] = U.chop_string(speed_str, ss[7], ctr, scr_st[5])

            self.print_str(data_fmt % (name_str, not s["is_paused"], state_str, size_str, s["progress"], seed_str, peer_str, speed_str),i+2, 0)
            
            if s["is_highlighted"]: self.w.attroff(CUR.A_REVERSE)
            i += 1

        i += 2
        cut = DT.datetime.now() - DT.timedelta(seconds = self.c["message_delay"])

        for l in filter(lambda l: l[1] > cut , self.l.get_ui()):
            self.print_message(l[0], 100, i)
            i += 1

        ll = self.l.get_last_log()
        if (ll[2] > cut):
            self.print_message(ll[0], ll[1], i)

        if ipt != "":
            self.print_with_tag(ipt, "magnet>", y-1)

        self.w.refresh()
        try:
            self.w.move(0, 0)
        except:
            pass

