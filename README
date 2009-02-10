Katipo - Checking your Webs
http://katipo.googlecode.com/

Copyright 2008 Robert Coup (robert@coup.net.nz)
Katipo is licensed under the Apache License, Version 2.0 - see LICENSE.

### Aim

Make a crawler for integration testing that will test all the accessible URLs
of a web application, check they're valid, and measure the response times
as a real user or a search engine bot would. Track changes over time so 
performance issues can be found and addressed early. Integrate nicely with 
existing build and test systems.

### Requirements

 * Django 1.0+          - http://www.djangoproject.com/
 * Twisted 8.1.0+       - http://www.twistedmatrix.com/ (specifically core, words, and names)
 * BeautifulSoup 3.0+   - http://crummy.com/software/BeautifulSoup
 * pyOpenSSL 0.6+       - http://pyopenssl.sourceforge.net/ (for https:// sites)

Currently Katipo has only been tested under Mac OS/X and Linux, but there's 
nothing particularly OS-specific about it.

### Quick Start

 1. Install the requirements and make sure they're in your Python path
 2. Run 'python katipo/manage.py syncdb' to initialise the database
 3. Run 'python katipo/manage.py runserver'
 4. Browse to http://localhost:8000/
 5. Go to "Manage Profiles", then "Create new Profile"
 6. Add a profile name (eg. "Example"), and the following settings:
      START_URLS = ('http://www.example.com',)
 7. Save the profile
 8. Run 'python katipo/runner.py Example' to perform a crawl
 9. Once its done, refresh the Katipo home page and your crawl should be listed
 10. Follow the links to explore the results

### Profile Options:
 
    START_URLS
    An explicit tuple of URLs to include or start crawling from. This is the 
    only required profile option.
    
    eg: ('http://example.com/', 'http://example.org/',)
    
    IGNORE_URL_MATCH
    A tuple of regular expressions of URLs to ignore and not crawl. They should
    match fully-qualified URLs.
    
    eg: (r'^http://example.com/dontcrawl/', r'\?(.*)foo=nocrawl(.*)$', r'^http://example.com/images/',)
    
    EXPECTED_ERRORS
    A tuple of (url,status) pairs for URLs that are expected to return non-2xx 
    response codes. URLs should be fully qualified including query arguments, 
    and status codes should be integers.
    
    eg: (('http://example.com/404/', 404), ('http://example.com/500/', 500),)

    EXTRA_HOSTS
    A tuple of hostnames to treat as 'internal' (ie. will be crawled). All 
    hosts from START_URLS are included automatically.
    
    eg: ('example.net', 'example.biz',)

    TEST_EXTERNALS
    A boolean value determining whether to check external URLs (only the 
    first/linked URL, none beyond that).

    PARSE_CONTENT_TYPES
    A tuple of regular expressions of content-types to parse for URLs.
    
    Default: (r'^text/', r'^application/xhtml+xml$',)

### Integrating with Build/Test systems

When calling runner.py, you need to specify a Profile name, but can also 
specify a Run name. This could be a build number or SVN revision number or
whatever you like. 

    python katipo/runner.py ExampleProfile build123

### ToDo List

Contributions or suggestions are welcome! Here's some of the things currently
on the radar:

 * Graphing of response time history for a URL
 * Alerts for response times that have dramatically changed
 * Better accuracy of response times (warm-up for server, multiple requests, ?)
 * Something like pystones, where overall performance of a site can be tracked 
   over time.
 * Cookie support
 * Stages or sequences of URLs
 * Ability to monitor/cancel a run
 * Test for presence/absence of text in specific URLs
 * Support for more tags: <frameset>, <map>, <style> ( @import / url() )
 * Smarter support for <link> tags
 * Ability to POST specific forms?
 * Support for robots.txt, particularly crawl rates
 * Flushing of old test results from the database
 * RSS feeds of results for tying into other systems

And some necessary ToDos so people might actually use it:

 * Document proper setup of the web interface (mod-wsgi, etc)
 * Set up better scripts for launching/etc that don't depend on the current
   directory as much
 * Checking dependency versions
 * Setuptools installer
 * PyPi
 * Support for older Python versions, Windows, etc (hey, they *might* work now ;) )

