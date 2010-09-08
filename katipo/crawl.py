import re
import urlparse
import logging
import datetime
import time

from twisted.web import client
import twisted.web.error
from twisted.internet import defer, task, reactor
import twisted.internet.error

from parse import HtmlParser, ParseError

class HTTPFetcher(client.HTTPPageGetter):
    elapsed_time = datetime.timedelta()
    
    def connectionMade(self):
        r = client.HTTPPageGetter.connectionMade(self)
        self._start_time = time.clock()
        return r
    
    def handleResponse(self, result):
        #FIXME: why does this get called before connectionLost?
        end_time = time.clock()
        self.elapsed_time = datetime.timedelta(seconds=end_time-self._start_time)
        self.factory.gotElapsedTime(self.elapsed_time)
        return client.HTTPPageGetter.handleResponse(self, result)
    
    def connectionLost(self, reason):
        if not self.elapsed_time:
            end_time = time.clock()
            self.elapsed_time = datetime.timedelta(seconds=end_time-self._start_time)
            self.factory.gotElapsedTime(self.elapsed_time)
        return client.HTTPPageGetter.connectionLost(self, reason)

class HTTPFetcherFactory(client.HTTPClientFactory):
    protocol = HTTPFetcher
    
    def __init__(self, url, headers=None):
        client.HTTPClientFactory.__init__(self, url, headers=headers, agent="Katipo/0.1~a1 (+http://code.google.com/p/katipo/wiki/Bot)", timeout=30, followRedirect=0)
        self.status = None
        self.elapsed_time = datetime.timedelta()
        self.deferred.addErrback(self._check_http_error)
        self.deferred.addCallback(
            lambda data: (data, int(self.status), self.response_headers, self.elapsed_time))
    
    def _check_http_error(self, failure):
        # attempt to turn non-200 errors into valid pages
        failure.trap(twisted.web.error.Error)
        
        if failure.value.status is not None:
            return failure.value.response
        else:
            return failure
    
    def gotElapsedTime(self, elapsed_time):
        self.elapsed_time = elapsed_time
    
    @staticmethod
    def getPage(url, contextFactory=None, *args, **kwargs):
        scheme, host, port, path = client._parse(url)
        factory = HTTPFetcherFactory(url, *args, **kwargs)
        if scheme == 'https':
            from twisted.internet import ssl
            if contextFactory is None:
                contextFactory = ssl.ClientContextFactory()
            reactor.connectSSL(host, port, factory, contextFactory)
        else:
            reactor.connectTCP(host, port, factory)
        return factory.deferred

class Crawler(object):
    # Content-types we try and parse for links
    PARSE_CONTENT_TYPES = (
        r'^text/',
        r'^application/xhtml+xml$',
    )
    
    def __init__(self, to_crawl, ignore_match=(), hosts=(), test_externals=True, parse_content_types_match=PARSE_CONTENT_TYPES, parser_class=HtmlParser):
        self.to_crawl_s = set(to_crawl)
        self.to_crawl = list(self.to_crawl_s)
        self.in_crawl = set()
        self.crawled = set()
        self.ignored = set()
        
        self.parser = parser_class and parser_class() or None
        self.log = logging.getLogger('katipo.Crawler')
        
        # our valid hosts are anything in the to_crawl list, and any specified hosts
        self.hosts = set([client._parse(u)[1] for u in to_crawl] + list(hosts))
        self.test_externals = test_externals
        
        # save the original regex strings so we can log them later for debugging
        self.re_ignore = tuple([(r, re.compile(r)) for r in ignore_match])
        self.re_content_types = tuple([(r, re.compile(r)) for r in parse_content_types_match])
        
    def crawl(self, concurrent=5):
        """ Call this to kick the whole thing off. """
        self.to_crawl_s = set(self.to_crawl)
        self.to_crawl = list(self.to_crawl_s)
        self.in_crawl = set()
        self.crawled = set()
        self.ignored = set()
        
        coop = task.Cooperator()
        # call this once only, then create multiple references to the generator it returns
        work = self._crawl()
        deferreds = [coop.coiterate(work) for i in xrange(concurrent)]
        d = defer.DeferredList(deferreds)
        return d
    
    def _crawl(self):
        """ A generator returning URL fetches """
        while True:
            for url in self.to_crawl:
                self.to_crawl_s.discard(url)
                d = self.fetch(url)
                # fetch() will return None for an invalid URL
                if d:
                    yield d
            
            if len(self.in_crawl):
                # we're still crawling something, so we need to pretend 
                # there's more to crawl in the meantime so the Cooperator
                # will keep querying us
                yield defer.succeed(None)
            else:
                break
    
    def fetch(self, url):
        """ 
        Fetch a single URL, first checking:
         - we haven't previously got it
         - we aren't fetching it right now
        """
        if url in self.crawled:
            self.log.debug("Skipping: %s (already crawled)", url)
            return
        elif url in self.in_crawl:
            self.log.debug("Skipping: %s (crawling already)", url)
            return
        elif url in self.ignored:
            self.log.debug("Skipping: %s (ignored)", url)
            return
        
        self.log.debug("Fetching: %s", url)
        self.in_crawl.add(url)
        d = HTTPFetcherFactory.getPage(url)
        
        d = d.addBoth(self._fetch_end, url)
        d = d.addCallback(self._fetch_load, url)
        d = d.addErrback(self._fetch_error, url)
        return d
    
    def _fetch_end(self, result, url):
        """ 
        Called after a fetch finishes (regardless of error/success). 
        Remove the URL from the currently-crawling list.
        """
        self.in_crawl.remove(url)
        self.crawled.add(url)
        return result
        
    def _fetch_load(self, result, url):
        """ 
        This is called when we get a valid response (including 404/500/etc).
        Basically we check the content-type is OK for parsing, parse the response,
        and add any valid links we find to the crawl list.
        """
        content, status, headers, elapsed_time = result
        content_type = headers.get("content-type", ('',))[0].split(";")[0].strip()
        
        self.log.info("Got %s: %s @ %s", url, status, str(elapsed_time))
        current_url_valid = (self.check_link(url) == True)
        
        links = set()
        
        redirects = headers.get("location", ())
        if redirects:
            if current_url_valid:
                for r in redirects:
                    links.add(urlparse.urljoin(url, r))
        elif self.parser:
            ct_parse = False
            for ct_s, ct_re in self.re_content_types:
                if ct_re.match(content_type):
                    ct_parse = True
                    break
            
            if not ct_parse:
                self.log.debug("Not parsing: %s (content_type=%s)", url, repr(content_type))
            else:
                links = set(self.parser.extractLinks(content, url))

        for link in links:
            valid = self.check_link(link)
            if valid != True:
                if valid == 'host' and self.test_externals and current_url_valid:
                    # test external link, but it'll stop for any links generated
                    # from that page (unless they point to one of our valid hosts).
                    self.log.debug("Testing external link: %s", link)
                    pass
                else:
                    self.log.debug("Skipping: %s (failed link-check)", link)
                    self.ignored.add(link)
                    continue
    
            if link not in self.to_crawl_s and link not in self.crawled and link not in self.in_crawl and link not in self.ignored:
                self.to_crawl.append(link)
                self.to_crawl_s.add(link)
        
        self.on_fetch(url, status, headers, elapsed_time, content_type, links, current_url_valid)
    
    def _fetch_error(self, failure, url):
        """ 
        This is called when an error occurs fetching a URL. It's not called when
        we get a valid response (even a 404/500/etc).
        """
        e = failure.value
        if isinstance(e, twisted.web.error.Error):
            self.log.info("HTTP Error %s: %s", url, e)
        elif isinstance(e, twisted.internet.error.DNSLookupError):
            self.log.info("DNS Error %s: %s", url, e)
        elif isinstance(e, ParseError):
            self.log.info("Parse Error %s: %s", url, e.message)
        else:
            self.log.warn("Unknown Error %s: %s", url, e)
        
        self.on_error(url, failure.value)
        
    def check_link(self, url):
        """ 
        Test whether we should fetch the specified URL. Look at:
            - that it uses http/https
            - hostname is in our okay-list
            - the URL doesn't match a regex in our ignore list
        
        *Important*: Returns either True on success, or a string error-code on failure.
        """
        scheme, host, port, path = client._parse(url)
        
        if scheme not in ('http', 'https'):
            self.log.debug('check_link: fail (scheme=%s), %s', scheme, url)
            return 'scheme'
        
        if host not in self.hosts:
            self.log.debug('check_link: fail (hosts), %s', url)
            return 'host'
        
        for (ign_s, ign_re) in self.re_ignore:
            if ign_re.search(url):
                self.log.debug('check_link: fail (regex %s), %s', repr(ign_s), url)
                return 'regex'
        
        return True
    
    def on_fetch(self, url, status, headers, elapsed_time, content_type, outgoing_links, is_internal):
        pass
    
    def on_error(self, url, error):
        pass
    
    def get_stats(self):
        return (len(self.crawled), len(self.in_crawl), len(self.to_crawl_s), len(self.ignored),)

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    from datetime import datetime
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print >>sys.stderr, "USAGE: %s URL..." % sys.argv[0]
        sys.exit(2)
    
    c = Crawler(to_crawl=sys.argv[1:])
    
    def printStats():
        print "\nSTATS: crawled=%d, crawling=%d, to-crawl=%d, ignored=%d\n" % c.get_stats()
    
    c.crawl().addBoth(lambda r: reactor.stop())
    task.LoopingCall(printStats).start(10.0)
    
    started_at = datetime.now()
    reactor.run()
    
    # Print a summary
    stats = c.get_stats()
    elapsed = datetime.now() - started_at
    printStats()
    print "TOTAL TIME: %s, crawl-rate=%0.1freqs/s" % (elapsed, stats[0]/elapsed.seconds)
