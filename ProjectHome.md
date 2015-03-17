# Katipo - Checking your Webs #

A crawler for testing of web applications.

## Aims ##

Make a crawler for integration testing that will test all the accessible URLs of a web application, check they're valid, and measure the response times as a real user or a search engine bot would. Track changes over time so performance issues can be found and addressed early. Integrate nicely with existing build and test systems.

## Getting Started ##

  * There aren't any releases yet, so check out the [source code](http://code.google.com/p/katipo/source/checkout) from trunk
  * Have a read of the [README](http://code.google.com/p/katipo/source/browse/trunk/README) file

### Requirements ###

  * [Python](http://www.python.org) 2.5+
  * [Django](http://www.djangoproject.com/) 1.0+
  * [Twisted](http://www.twistedmatrix.com/) 8.1.0+ (specifically core, words, and names)
  * [BeautifulSoup](http://crummy.com/software/BeautifulSoup) 3.0+
  * [pyOpenSSL](http://pyopenssl.sourceforge.net/) 0.6+ (for https:// sites)

All are installable via setuptools (`easy_install`). Currently there aren't any checks for the versions of dependencies, so (for example) if you have pre-1.0 Django on your system you'll get weird errors happening.

Katipo has only been tested under Mac OS/X and Linux, but there's nothing particularly OS-specific about it.

## Help!? ##

Head over to the [Katipo Discussion group](http://groups.google.com/group/katipo) and get in touch.

## What's next? ##

Contributions or suggestions are welcome (create an issue or post to the discussion group)! Here's some of the things currently on the radar:

  * Graphing of response time history for a URL
  * Alerts for response times that have dramatically changed
  * Better accuracy of response times (warm-up for server, multiple requests, ?)
  * Something like pystones, where overall performance of a site can be tracked over time.
  * Cookie support
  * Stages or sequences of URLs
  * Ability to monitor/cancel a run
  * Test for presence/absence of text in specific URLs
  * Support for more tags: `<frameset>`, `<map>`, `<style>` (`@import`/`url()`)
  * Smarter support for `<link>` tags
  * Ability to POST specific forms?
  * Support for `robots.txt`, particularly crawl rates
  * Flushing of old test results from the database
  * RSS feeds of results for tying into other systems

And some necessary ToDos so people might actually use it:

  * Document proper setup of the web interface (mod-wsgi, etc)
  * Set up better scripts for launching/etc that don't depend on the current directory
  * Checking dependency versions
  * Setuptools installer
  * PyPi
  * Support for older Python versions, Windows, etc (hey, they **might** work now ;) )
  * Turn this list of ToDo's into Google Code issues.

## Other Stuff ##

### Why "Katipo"? ###

According to Wikipedia:

> The [katipo](http://en.wikipedia.org/wiki/Katipo) (Latrodectus katipo) is an endangered, venomous spider native to [New Zealand](http://en.wikipedia.org/wiki/New_Zealand). It is a widow spider and is related to the Australian redback spider, and the North American black widow spiders. Katipo is a Māori name and means "night-stinger".

It's a spider, it crawls. Maybe it'll eat bugs, or sting you into improving performance. Enough with the metaphors already ;)

### History ###

The initial implementation was built by [Robert Coup](http://rob.coup.net.nz/) of [Koordinates](http://koordinates.com) for internal use and open sourced in January 2009.