#!/usr/bin/python
"""
lcdScroll-RSS.py
Author             :  Martin Coleman 
Creation Date      :  14/02/2022

Free and open for all to use.  But put credit where credit is due.

OVERVIEW:-----------------------------------------------------------------------
Obtian data from an RSS feed and display it on an LCD
"""
from time import sleep
import time
import pifacecad
from lcdScroll import Scroller
import feedparser
import sys

rawfeed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml?edition=uk")
feedtitle = "BBC News - UK"


class App(pifacecad.PiFaceCAD):

    def __init__(self):
        pifacecad.PiFaceCAD.__init__(self)

        # setup the LCD:

        self.lcd.clear()
        self.lcd.blink_off()
        self.lcd.cursor_off()
        self.lcd.backlight_on()
        self.speed = .0 # How fast to scroll the lcd

        # main loop:
        while True:
            try:
                for i in range (5):
                    self.lcd.clear() # Clears at the start of each new title
                    title = feedtitle
                    feed = rawfeed['entries'][i]['title']
                    #print (feed)
                    lines = [title,feed]
                    # Create our scroller instance:
                    scroller = Scroller(lines=lines)
                    message = "\n".join(lines)
                    t_end = time.time() + 5 * 6
                    while time.time() < t_end:
                        # Get the updated scrolled lines, and display:
                        message = scroller.scroll()
                        self.lcd.write(message)
                        sleep(self.speed)
            except KeyboardInterrupt:
                    # Clear display.
                    self.lcd.blink_off()
                    self.lcd.cursor_off()
                    self.lcd.backlight_off()
                    self.lcd.clear()
                    sys.exit()

        
if __name__ == "__main__":
    App()

