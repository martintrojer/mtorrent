# About
mtorrent is a fast, lightweight, head-less, curses based, configurable torrent client. 

Uses the [libtorrent-rasterbar](http://www.libtorrent.org "libtorrent-rasterbar") library.

Mainly aimed for use in "closet-servers" such as NAS boxes.

## Main Features

* Lightweight and CPU/memory efficient
* Downloading and seeding of .torrent files
* Simple curses based UI
* Magnet URIs
* DHT
* PEX
* UPNP
* Read-only HTML session information
* Configurable via a configuration file

Licensed under GPL3.

Tested on Linux and OSX.

# Installation

mtorrent depends on Python(2.6 or 2.7) and libtorrent-rasterbar [python bindings](http://www.rasterbar.com/products/libtorrent/python_binding.html "python bindings"). Check that you have both installed before proceeding.

    $ python
    Python 2.6.6 (r266:84292, Dec 27 2010, 10:20:06) 
    [GCC 4.4.5] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import libtorrent
    >>> 

Install mtorrent with the provided install script

    $ sudo python setup.py install

Copy the configuration file and modify to your taste

    $ cp example.mtorrentrc ~/.mtorrentrc
    $ nano ~/.mtorrentrc

Create the mtorrent work directory plus the session and watch folders (these are the default values)

    $ cd ~
    $ mkdir mtorrent
    $ cd mtorrent
    $ mkdir session
    $ mkdir watch
    
# Usage

mtorrent is aimed to head-less servers which you typically remote into via ssh. The best way to run it is via a tool such as [screen](http://www.gnu.org/software/screen "screen"). 

A typical session to start mtorrent could be

    $ ssh my-server
    $ cd mtorrent
    $ screen mtorrent 

And then later to check to the status

    $ ssh my-server
    $ screen -r

## UI

The curses based UI supports the following commands.

* Arrow up / down 
Move the highlighted torrent file
* R (capital R)
Stop and remove the torrent file from the session
* s 
Pause the torrent
* q
Quit mtorrent (this might take a while to write out all resume data)
* ENTER
Enter/Exit the magnet uri input mode (see below)

## Adding .torrent files

.torrent files are added by copying .torrent files into the "watch" path (see configuration file). mtorrent scans this folder ever so often and automatically adds any torrent to the current session.

When torrents are removed (with the R UI command) the .torrent file in the watch path will also be deleted.

Please note the just removing the .torrent file from the watch path will not stop and remove the torrent from the current session.

## Adding Magnet URIs

Magned URIs are added (pasted) directly into the UI. The Enter key is used to toggle the magnet input mode. While you are in this mode a "magnet> " prompt will show at the bottom on the screen. 

The typical workflow for adding magnet URIs are

* Copy the URI to your clipboard in a browser
* Bring up the mtorrent UI (probably 'screen -r')
* Press ENTER to enter the magnet input mode
* Paste the magnet URI into to the mtorrent UI
* Press ENTER

## HTML read-only status page

If configured accordingly, mtorrent will write out an HTML file with the current status of the session. This can we viewed with a web browser. When setting up your web server, make sure the .png and .css files from the mtorrent "web" source folder is readable from the generated HTML file.

# Configuration

The example.mtorrentc should be pretty self explanatory. If in doubts, check the [libtorrent docs](http://www.rasterbar.com/products/libtorrent/manual.html "libtorrent docs").