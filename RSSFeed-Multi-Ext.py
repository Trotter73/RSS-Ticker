#!/usr/bin/python
"""
RSSFeed-Multi.py
Author             :  Martin Coleman with major contributions by Raspberry Pi forum user ghp
Creation Date      :  03/03/2022

Free and open for all to use.  But put credit where credit is due.

Use the rocker switch to flip between feeds, button 4 (the one on it's own) will shutdown.

In this version the RSS feeds are read in from /boot/rss-feeds.txt , this enables feeds to
be added and removed on a Windoze machine 

OVERVIEW:-----------------------------------------------------------------------
Obtian data from an RSS feeds and display it on an LCD
"""

import pifacecad
try:
    from lcdScroll import Scroller
except ImportError:
    print ("Please ensure lcdScroll.py is in the current directory")
try:    
    import feedparser
except ImportError:
    print ("The feedparser module is missing! Please run; sudo pip install feedparser and try again.")    
import sys
import threading
import time
import copy
import os
import ast

with open("/boot/rss-feeds.txt", "r") as data:
    RSS_FEEDS = ast.literal_eval(data.read())

class RSSFeed(object):
    def __init__(self, feed_name, feed_url):
        self.feed_name = feed_name
        self.feed_url = feed_url

class FeedViewer:
    def __init__(self, cad):
        self.cad = cad
        self.cad.lcd.backlight_on()
        self.cad.lcd.blink_off()
        self.cad.lcd.cursor_off()

    def start(self, feed):
        self.current_feed = feed

        self.run = True
        self.stopped_event = threading.Event()

        self.thread_update = threading.Thread(target=self._update, name="update")
        self.thread_update.start()

    def stop(self):
        self.run = False
        self.stopped_event.wait()
        self.stopped_event.clear()

    def terminate(self):
        cad.lcd.blink_off()
        cad.lcd.cursor_off()
        cad.lcd.backlight_off()
        cad.lcd.clear()

    def _update(self):
        """ running in a thread; rolling feeds to lcd"""
        speed_time = 0.01 # How fast to scroll the lcd
        current_position = 0
        rawfeed=feedparser.parse(self.current_feed.feed_url)
        self.cad.lcd.clear()

        while self.run:
            try:
                feed = rawfeed['entries'][current_position]['title']
            except Exception:
                # most possibly end of feed arrived
                current_position = 0
                continue

            title = self.current_feed.feed_name
            lines = [title,feed]

            #  Create our scroller instance:
            scroller = Scroller(lines=lines)
            t_end = time.time() + 60 # How long to scroll each entry of the feed, in seconds.
            while time.time() < t_end:
                if not self.run: break
                #Get the updated scrolled lines, and display:
                message = scroller.scroll()
                self.cad.lcd.write(message)

                self._sleep(speed_time)

            current_position += 1
        self.stopped_event.set()

    def _sleep(self, t):
        """a stoppable time.sleep()"""
        t_end = time.time() + t

        while time.time() < t_end:
            if not self.run: break
            time.sleep(0.05)

# listener cannot deactivate itself so we have to wait until it has
# finished using a threading.Barrier.
# global end_barrier
end_barrier = threading.Barrier(2)

class RSSController(object):
    def __init__(self, cad, feeds, feed_index=0):
        self.feeds = feeds
        self.feed_index = feed_index
        self.lock = threading.Lock()

        with self.lock:
            self.viewer = FeedViewer(cad)
            current_feed = copy.copy( self.feeds[self.feed_index] )
            self.viewer.start( current_feed)

    def next_feed(self, event=None):
        with self.lock:
            self.feed_index = (self.feed_index + 1) % len(self.feeds)
            self.viewer.stop()
            current_feed = copy.copy( self.feeds[self.feed_index] )
            self.viewer.start( current_feed)


    def previous_feed(self, event=None):
        with self.lock:
            self.feed_index = (self.feed_index - 1) % len(self.feeds)
            self.viewer.stop()
            current_feed = copy.copy( self.feeds[self.feed_index] )
            self.viewer.start( current_feed)

    def stop(self):
        with self.lock:
            self.viewer.stop()
            self.viewer.terminate()


if __name__ == "__main__":

        feeds = \
         [RSSFeed(s['feed_name'], s['url']) for s in RSS_FEEDS]

        cad = pifacecad.PiFaceCAD()

        # global rssdisplay
        rssdisplay = RSSController(cad, feeds)

        # wait for button presses
        switchlistener = pifacecad.SwitchEventListener(chip=cad)
        switchlistener.register(4, pifacecad.IODIR_ON, end_barrier.wait)
        switchlistener.register(6, pifacecad.IODIR_ON, rssdisplay.previous_feed)
        switchlistener.register(7, pifacecad.IODIR_ON, rssdisplay.next_feed)
        switchlistener.activate()

        end_barrier.wait()  # wait unitl exit
        switchlistener.deactivate()
        rssdisplay.stop()
        cad.lcd.write("Shutdown In 5")
        time.sleep(5)
        cad.lcd.clear()
        os.system("sudo shutdown -h now")
        #sys.exit() # Uncomment this and comment the above to exit rather than shutdown.
        
        
