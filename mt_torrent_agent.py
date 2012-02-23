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

# Agent to serialize all communication with libtorrent

import mt_logger as L
import mt_utils as U

import threading as T
import Queue as Q
import libtorrent as LT
import pdb as P

class TorrentAgent(T.Thread):
    def __init__(self, config, logger):
        T.Thread.__init__(self)
        self.c = config
        self.q = Q.Queue()
        self.l = logger
        self.handle_by_name = {}
        self.highlight = None

        self.session = LT.session()

        settings = self.session.settings()
        settings.user_agent = self.c["version_short"]
        settings.auto_upload_slots_rate_based = self.c["auto_upload_slots"]
        settings.announce_to_all_trackers = self.c["ann_all_trackers"]
        settings.optimize_hashing_for_speed = self.c["optimize_hash_speed"]
        settings.disk_cache_algorithm = self.c["disk_cache_algo"]
        settings.use_dht_as_fallback = self.c["dht_as_fallback"]
        self.session.set_settings(settings)

        # Load session state
        try:
            f = open(self.c["session_file"],'rb')
            self.l.log("TorrentAgent:loading session state")
            self.session.load_state(LT.bdecode(f.read()))
            f.close()
        except:
            self.l.log("TorrentAgent:failed to read session state " + self.c["session_file"], L.WARN)

        # Start extensions
        self.session.add_extension(LT.create_ut_metadata_plugin)
        self.session.add_extension(LT.create_ut_pex_plugin)
        self.session.add_extension(LT.create_smart_ban_plugin)

        # Start DHT and UPNP
        if self.c["use_dht"]:
            self.session.add_dht_router(self.c["dht_router1"][0], self.c["dht_router1"][1])
            self.session.add_dht_router(self.c["dht_router2"][0], self.c["dht_router2"][1])
            self.session.add_dht_router(self.c["dht_router3"][0], self.c["dht_router3"][1])
            self.session.start_dht()
        self.session.listen_on(self.c["listen_on"][0], self.c["listen_on"][1])
        if self.c["use_upnp"]:
            self.session.start_upnp()

    def __teardown(self):
        self.l.log("TorrentAgent:stopping")
        self.session.pause()
        resume_ctr = 0

        # Save session state for individual torrents
        for h, f in self.handle_by_name.values():
            if h.is_paused(): continue
            if not h.is_valid(): continue
            if not h.has_metadata(): continue
            self.l.log("TorrentAgent:saving resume data for " + h.name(), L.DBG)
            h.save_resume_data()
            resume_ctr += 1

        self.l.log("TorrentAgent:waiting for resume data...")

        while resume_ctr > 0:
            a = self.session.wait_for_alert(30 * 1000)    # 30 secs
            if a == None:
                self.l.log(
                    "TorrentAgent:aborting with outstanding torrents to save resume data", 
                    L.WARN)
                break

            dummy = self.session.pop_alert()
            if a.what() == "save resume data complete":
                filename = self.c["session_path"]+"/"+str(a.handle.info_hash())+".resume"
                try:
                    f = open(filename,'wb')
                    self.l.log("TorrentAgent:writing resume data to " + filename, L.DBG)
                    self.l.log_ui("Writing resume data to " + filename)
                    f.write(LT.bencode(a.resume_data))
                    f.close()
                except:
                    self.l.log("TorrentAgent:error saving resume data " + filename, L.ERR)
            elif a.what() == "save resume data failed": 
                self.l.log_ui("No resume data for " + a.handle.name())
                self.l.log(
                    "TorrentAgent:error getting resume data for " + a.handle.name() + 
                    " " + a.what(), L.WARN)
            else:
                self.l.log("TorrentAgent:unknown alert received " + a.what(), L.WARN)
                continue

            resume_ctr = resume_ctr - 1
            
        # Save state for the entire session
        self.l.log("TorrentAgent:saving session state", L.DBG)
        try:
            f = open(self.c["session_file"],'wb')
            f.write(LT.bencode(self.session.save_state()))
            f.close()
        except:
            self.l.log("TorrentAgent:error save session file " + self.c["session_file"], L.ERR)

    def __check_dups(self, name):
        return filter(lambda n: n == name, self.handle_by_name.keys()) != []

    def __get_resume_data(self, hash):
        try:
            resume_name = self.c["session_path"]+"/"+hash+".resume"
            self.l.log("TorrentAgent:reading resume data from " + resume_name, L.DBG)
            f = open(resume_name, 'rb')
            data = f.read()
            f.close()
            return LT.bdecode(data)
        except:
            self.l.log("TorrentAgent:error reading resume data from " + resume_name, L.DBG)
            return ""

    def __setup_handle(self, h):
        h.set_max_connections(self.c["max_connections"])
        h.set_max_uploads(self.c["max_uploads"])
        h.set_ratio(self.c["ratio"])
        h.set_upload_limit(self.c["upload_limit"])
        h.set_download_limit(self.c["download_limit"])
        h.resolve_countries(self.c["resolve_countries"])

    def __add_torrent(self, filename):
        self.l.log("TorrentAgent:adding torrent " + filename)

        if self.__check_dups(filename):
            self.l.log("TorrentAgent:skipping, already added " + filename)
            return 

        torrent_data = None
        try:
            f = open(filename, 'rb')
            torrent_data = LT.bdecode(f.read())
            f.close()
        except:
            self.l.log("TorrentAgent:error reading from " + filename, L.ERR)
            return

        try:
            info = LT.torrent_info(torrent_data)
        except:
            self.l.log("TorrentAgent:error adding torrent, corrupt file? " + filename, L.ERR)
            return

        resume_data = self.__get_resume_data(str(info.info_hash()))
        
        h = self.session.add_torrent(info, self.c["save_path"],
                                     resume_data=resume_data,
                                     storage_mode=self.c["storage_mode"])

        self.__setup_handle(h)
        self.handle_by_name[filename] = (h, False)

    def __scan_and_add(self, path):
        self.l.log("TorrentAgent:scanning path " + path, L.DBG)
        files = {"torrent":[], "magnet": []}
        try:
            files = U.scan_dir(path)
        except:
            self.l.log("TorrentAgent:failed to scan dir " + path, L.WARN)

        for t in files["torrent"]:
            if not self.__check_dups(t):
                self.__add_torrent(t)
        for m in files["magnet"]:
            try:
                f = open(m, "rb")
                uri = f.read()
                f.close()
                if not self.__check_dups(uri):
                    info_hash = m.split(".magnet")[0]
                    self.__add_magnet(uri, info_hash)
            except:
                self.l.log("TorrentAgent:error reading from " + m, L.ERR)

    def __add_magnet(self, uri, info_hash):
        self.l.log("TorrentAgent:adding magnet " + uri)

        if self.__check_dups(uri):
            self.l.log("TorrentAgent:skipping, already added " + uri)
            return 

        resume_data = self.__get_resume_data(info_hash)

        params = {"save_path":self.c["save_path"], "resume_data":resume_data, 
                  "storage_mode":self.c["storage_mode"],
                  "paused":self.c["start_as_paused"], 
                  "duplicate_is_error":self.c["dup_is_error"],
                  "auto_managed":self.c["auto_managed"]}
        
        try:
            h = LT.add_magnet_uri(self.session, uri, params)
        except:
            self.l.log("TorrentAgent:error adding magnet, malformed URI? " + uri, L.ERR)
            return

        try:
            fname = self.c["watch_path"] + "/" + str(h.info_hash()) + ".magnet"
            self.l.log("TorrentAgent:writing magnet restart file " + fname, L.DBG)
            f = open(fname, "wb")
            f.write(uri)
            f.close()
        except:
            self.l.log("TorrentAgent:error writing magnet restart file " + fname, L.ERR)

        self.__setup_handle(h)
        self.handle_by_name[uri] = (h, True)

    def __remove_torrent(self, name):
        self.l.log("TorrentAgent:removing torrent " + name)
        
        if not self.handle_by_name.has_key(name):
            self.l.log("TorrentAgent:error removing torrent, not in current session " + 
                       name, L.ERR)
            return None

        h, is_magnet = self.handle_by_name.pop(name)
        self.highlight = None

        # remove any resume file
        U.remove_file(self.c["session_path"] + "/" + str(h.info_hash()) + ".resume", self.l)

        # remove the source file
        if is_magnet:
            name = self.c["watch_path"] + "/" + str(h.info_hash()) + ".magnet"        
        U.remove_file(name, self.l)

        # remove the torrent from the session
        try:
            self.session.remove_torrent(h)
        except:
            self.l.log("TorrentAgent:internal error remove torrent " + name, L.ERR)
            return None

        return name

    def __remove_highlighted(self):
        n = filter(lambda k: self.handle_by_name[k] == self.highlight, self.handle_by_name)
        if len(n) == 1:
            return self.__remove_torrent(n[0])

    def __remove_all(self):
        res = []
        for k in self.handle_by_name.keys():
            res.append(self.__remove_torrent(k))
        return res

    def __toggle_pause(self, name):
        self.l.log("TorrentAgent:toggle_pause " + name)

        if not self.handle_by_name.has_key(name):
            self.l.log("TorrentAgent:torret not in session " + name, L.ERR)
            return None
        else:
            h, im = self.handle_by_name[name]
            if h.is_paused():
                h.resume()
            else:
                h.pause()

        return name

    def __toggle_highlighted(self):
        n = filter(lambda k: self.handle_by_name[k] == self.highlight, self.handle_by_name)
        if len(n) == 1:
            return self.__toggle_pause(n[0])

    def __toggle_all(self):
        keys = self.handle_by_name.keys()
        for k in keys:
            self.__toggle_pause(k)
        return keys

    def __move_highlight(self, delta):
        vs = self.handle_by_name.values()
        if len(vs) == 0:
            self.highlight = None
        elif self.highlight == None:
            self.highlight = vs[0]
        else:
            idx = vs.index(self.highlight)
            new_idx = (idx + delta) % len(vs)
            self.highlight = vs[new_idx]
        self.l.log("TorrentAgent:highlight is now " + str(self.highlight), L.DBG)
    
    def __get_state(self):
        res = []        
        i = 0
        for k in self.handle_by_name.keys():
            h, is_magnet = self.handle_by_name[k]
            status = h.status()

            size = 0
            try:
                # this sometimes fails (for magnets without meta data)
                size = h.get_torrent_info().total_size()
            except:
                pass

            states = ['queued for checking', 'checking files', 'downloading metadata',
                      'downloading', 'finished', 'seeding', 'allocating',
                      'checking resume data']

            state_str = ""

            try:
                state_str = states[status.state]
            except:
                self.l.log("TorrentAgent:unknown state for " + k, L.WARN)
                state_str = "unknown"

            res.append({"name" : h.name(), 
                        "source" : k,
                        "hash" : str(h.info_hash()),
                        "size" : size,
                        "status" : state_str,
                        "progress" : status.progress * 100,
                        "down_rate" : status.download_rate,
                        "up_rate" : status.upload_rate,
                        "seeds" : status.num_seeds,
                        "seeds_total" : status.list_seeds,
                        "peers" : status.num_peers,
                        "peers_total" : status.list_peers,
                        "is_paused" : h.is_paused(),
                        "is_highlighted": (h, is_magnet) == self.highlight,
                        "is_magnet": is_magnet})
        return res

    def run(self):
        self.l.log("TorrentAgent:starting")
        running = True
        while running:
            item = self.q.get()
            self.l.log("TorrentAgent:req:" + item[0], L.DBG)
            msg = item[0]
            if msg == "add_torrent":
                self.__add_torrent(item[1])
            elif msg == "scan_and_add":
                self.__scan_and_add(item[1])
            elif msg == "add_magnet":
                self.__add_magnet(item[1], item[2])
            elif msg == "remove_torrent":
                self.__remove_torrent(item[1])
            elif msg == "remove_highlighted":
                item[1].put(self.__remove_highlighted())
            elif msg == "remove_all":
                item[1].put(self.__remove_all())
            elif msg == "toggle_pause":
                self.__toggle_pause(item[1])
            elif msg == "toggle_highlighted":
                item[1].put(self.__toggle_highlighted())
            elif msg == "toggle_all":
                item[1].put(self.__toggle_all())
            elif msg == "move_highlight":
                self.__move_highlight(item[1])
            elif msg == "get_state":
                item[1].put(self.__get_state())
            elif msg == "stop":
                self.__teardown()
                running = False
                item[1].put(True)
            else:
                self.l.log("TorrentAgent:unknown message received " + str(msg), L.ERR)
            self.q.task_done()

    # Interface functions, called from other threads
    
    def __action_with_res(self, action):
        q = Q.Queue()
        self.q.put([action, q])
        r = q.get()
        q.task_done()
        return r

    def add_torrent(self, fname):
        self.q.put(["add_torrent", fname])

    def scan_and_add(self, path):
        self.q.put(["scan_and_add", path])

    def add_magnet(self, uri, info_hash):
        self.q.put(["add_magnet", uri, info_hash])

    def remove_torrent(self, name):
        self.q.put(["remove_torrent", name])

    def remove_highlighted(self):
        return self.__action_with_res("remove_highlighted")

    def remove_all(self):
        return self.__action_with_res("remove_all")

    def toggle_pause(self, name):
        self.q.put(["toggle_pause", name])

    def toggle_highlighted(self):
        return self.__action_with_res("toggle_highlighted")

    def toggle_all(self):
        return self.__action_with_res("toggle_all")

    def highlight_up(self):
        self.q.put(["move_highlight", -1])

    def highlight_down(self):
        self.q.put(["move_highlight", 1])

    def get_state(self):
        return self.__action_with_res("get_state")

    def stop(self):
        #blocks until teardown is complete
        return self.__action_with_res("stop")
