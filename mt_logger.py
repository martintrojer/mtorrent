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

# A logger agent

import threading as T
import Queue as Q
import datetime as DT

NONE = 5
ERR  = 4
WARN = 3
INFO = 2
DBG  = 1
ALL  = 0

class Logger(T.Thread):
    def __init__(self, config):
        T.Thread.__init__(self)
        self.c = config
        self.q = Q.Queue()
        self.file = open(self.c["log_file"],'a+')
        self.last_log = ["",0,DT.datetime.now() - DT.timedelta(minutes=1)]
        self.ui_logs = []

    def __del__(self):
        self.file.close()

    def __do_log(self, s, level):
        datestr = DT.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        levelstr = ""
        if level == ERR:
            levelstr = "Error"
        elif level == WARN:
            levelstr = "Warning"
        elif level == INFO:
            levelstr = "Info"
        elif level == DBG:
            levelstr = "Debug"

        logstr = datestr + " " + levelstr + " " + s
        if level >= self.c["log_level"]:
            self.file.write(logstr)
            self.file.write("\n")
            
            if self.c["log_echo"]:
                print(logstr)

        if level >= WARN:
            self.last_log = [s, level, DT.datetime.now()]

    def __do_log_ui(self, s):
        self.ui_logs.append([s, DT.datetime.now()])

    def run(self):
        self.__do_log("LoggerAgent:starting", INFO)
        running = True
        while running:
            item = self.q.get()
            self.__do_log("LoggerAgent:req:" + item[0], DBG)
            msg = item[0]
            if msg == "log":
                self.__do_log(item[1], item[2])
            elif msg == "log_ui":
                self.__do_log_ui(item[1])
            elif msg == "get_last":
                item[1].put(self.last_log)
            elif msg == "get_ui":
                item[1].put(self.ui_logs)
            elif msg == "stop":
                running = False
            else:
                self.__do_log("LoggerAgent:unknown message received " + str(msg), ERR)
            self.q.task_done()
    
    # Interface functions, called from other threads

    def __action_with_res(self, action):
        q = Q.Queue()
        self.q.put([action, q])
        r = q.get()
        q.task_done()
        return r

    def log(self, s, level=INFO):
        if level >= self.c["log_level"]:
            self.q.put(["log",s,level])

    def log_ui(self, s):
        self.q.put(["log_ui", s])

    def get_last_log(self):
        return self.__action_with_res("get_last")

    def get_ui(self):
        return self.__action_with_res("get_ui")
 
    def stop(self):
        self.q.put(["stop"])
