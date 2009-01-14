from BeautifulSoup import BeautifulSoup
import urlparse

class ParseError(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.__dict__.update(kwargs)
        
    def __str__(self):
        return "%s (%s)" % (self.message, getattr(self, 'url', "No URL"))

class HtmlParser(object):
    # list of tags to look for
    # by default, just grab the URL from the specified attribute. To specify a
    # custom parser, put True as the value, and define a process_<tag>(self, tag) method
    TAGS = {
        'a' : 'href',
        'img' : 'src',
        'script' : 'src',
        'iframe' : 'src',
        'object' : 'src',
        'link' : 'rel',
        'form' : True,          # only GET forms
        'meta' : True,          # meta-refresh
        #'frameset' : True,
        #'map' : True,
        #'style' : True,        # @import, url()
    }
    
    def extractLinks(self, content, content_url=''):
        """ 
        Extract links from a HTML document. 
        Parses the document using BeautifulSoup, then returns absolute URLs 
        parsed from tags specified by Parser.TAGS. Doesn't do any filtering of 
        duplicate URLs.
        
        content: the current document
        content_url: the URL to the current document, for building absolute URLs
        """
        try:
            soup = BeautifulSoup(content, convertEntities=BeautifulSoup.HTML_ENTITIES)
        except Exception, e:
            raise ParseError("Couldn't parse HTML", url=content_url, source=e)
        
        for tag in soup.findAll(self.TAGS):
            links = self.process(tag)
            for l in links:
                url = l.geturl()
                if content_url:
                    url = urlparse.urljoin(content_url, url)
                yield str(url)
    
    def process(self, tag):
        """ Extract any URLs from a particular HTML element. """
        if self.TAGS[tag.name] is True:
            links = getattr(self, 'process_'+tag.name)(tag)
        else:
            links = self.process_default(tag, self.TAGS[tag.name])
        
        r_links = []
        if links:
            for link in links:
                u = urlparse.urlsplit(link)
                if u.scheme in ('', 'http', 'https'):
                    # ignore mailto:// javascript:// ftp:// etc
                    if u.netloc or u.path or u.query:
                        # skip fragment-only urls (eg. #bookmark)
                        r_links.append(u)
        
        return r_links
    
    def process_default(self, tag, attr):
        """ The default tag processor - extracts the specified attribute. """
        a = tag.get(attr, '').strip()
        if a:
            return (a,)
    
    def process_form(self, tag):
        """ Only return URLs for FORMs that use the GET method. """
        if tag.get('method', 'get').lower() == 'get':
            return self.process_default(tag, 'action')
    
    def process_meta(self, tag):
        """ Find the URL from a meta-refresh tag. Ignore refreshes to the same URL (ie. no url= part). """
        if tag.get('http-equiv', '').lower() == 'refresh':
            rc = tag.get('content', '').split(';', 1)
            if len(rc) >= 2:
                rc_url = rc[1].strip()
                if rc_url.startswith('url='):
                    return (rc_url[4:],)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] != "HtmlParser":
        print "Usage: %s HtmlParser [content-url] < content.html" % sys.argv[0]
        sys.exit(2)
    
    if sys.argv[1] == 'HtmlParser':
        p = HtmlParser()
    
    contentUrl = (len(sys.argv) >= 3) and sys.argv[2] or ''
    for link in p.extractLinks(sys.stdin.read(), contentUrl):
        print link
