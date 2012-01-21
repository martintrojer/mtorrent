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

# Collection of helper functions

import mt_logger as L

import datetime as DT
import os

def readable_size(size):
    i = 0
    units = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    while size > 1024:
        size = size / 1024
        i += 1
    return "%.2f%s" % (size, units[i])

# cuts and pads the string to get the "scrolling" effect
def chop_string(s, size, ctr, state):
    l = len(s)
    if size > l:
        return s, state

    rstate = state
    if ctr%(l-size+1) == 0:
        rstate = not state

    start = 0
    end = ctr%(l-size+1)

    if not rstate:
        start = ctr%(l-size+1)
        end = l - size

    return s[abs(end-start):], rstate

def remove_file(name, logger):
    try:
        os.remove(name)
    except:
        logger.log("Error removing file " + name, L.DBG)
        
def scan_dir(dir):
    res = {"torrent":[], "magnet":[]}
    for name in os.listdir(dir):
        if name.find(".magnet") != -1:
            res["magnet"].append(dir+"/"+name)
        elif name.find(".torrent") != -1:
            res["torrent"].append(dir+"/"+name)
    return res
    
def export_html(config, states, logger):
    logger.log("HTMLexport: starting", L.DBG)

    res = ""
    res += "<HTML><HEAD>"
    res += "<TITLE>" + config["version_short"] + "</TITLE>"
    res += "<LINK REL='stylesheet' TYPE='text/css' HREF='mtorrent.css'/>"
    res += "</HEAD><BODY>"
    res += "<H2>" + config["version_long"] + "</H2>"
    res += "<TABLE ID='mtorrent' align='center' SUMMARY='Running Torrents'>"
    res += "<THEAD><TR><TH>Name</TH><TH>A</TH><TH>Status</TH><TH>Size</TH><TH>Done</TH><TH>Seeds</TH><TH>Peers</TH><TH>Down</TH><TH>Up</TH></TR></THEAD>"
    res += "<TBODY>"

    for s in states:
        logger.log("HTMLexport:processing " + str(s), L.DBG)
            
        seed_str = "%d(%d)" % (s["seeds"], s["seeds_total"])
        peer_str = "%d(%d)" % (s["peers"], s["peers_total"])
        size_str = readable_size(s["size"])
        down_str = readable_size(s["down_rate"])
        up_str = readable_size(s["up_rate"])

        res += "<TR><TD>%s</TD><TD>%d</TD><TD>%s</TD><TD>%s</TD><TD>%.2f</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD><TD>%s</TD></TR>" % (s["name"], not s["is_paused"], s["status"], size_str, s["progress"], seed_str, peer_str, down_str, up_str)

    res += "</TBODY></TABLE>"
    res += "<DIV ID='foot'>"
    res += DT.datetime.now().strftime("%y-%m-%d %H:%M:%S")
    res += "<BR/>Copyright (c) 2010 Martin Trojer (martin.trojer@gmail.com)"
    res += "</DIV>"
    res += "</BODY></HTML>"

    return res
