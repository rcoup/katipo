#!/usr/bin/env python

import re
import os
import datetime
import logging

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'katipo.settings'

from katipo.models import Profile, Run, Url
from katipo.crawl import Crawler

class Runner(object):
    def __init__(self, profile_name):
        self.log = logging.getLogger('katipo.Runner')
        
        try:
            self._profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist, e:
            raise Exception("Profile '%s' not found" % profile_name)
            
        self._expected_errors = tuple([(re.compile(eu),ec) for eu,ec in self._profile.expected_errors])
    
    def run(self, run_id=''):
        from twisted.internet import reactor
        
        self.log.debug("Creating crawler, start-urls=%d", len(self._profile.start_urls))
        
        c = Crawler(to_crawl=self._profile.start_urls, 
                    ignore_match=self._profile.ignore_url_match, 
                    hosts=self._profile.extra_hosts,
                    test_externals=self._profile.test_externals,
                    parse_content_types_match=self._profile.parse_content_types)
        
        def _crawl_page_fetch(url, status, headers, elapsed_time, content_type, outgoing_links, is_internal):
            ru, created = Url.objects.get_or_create(url=url, run=self._run)
            ru.status_code=status
            ru.elapsed_time=elapsed_time
            ru.is_internal=is_internal
            
            for e_url, e_code in self._expected_errors:
                if e_url.search(url):
                    if status == e_code:
                        ru.result = Url.RESULT_GOOD
                    else:
                        ru.result = Url.RESULT_BAD
                    break
            else:
                if status >= 200 and status < 400:
                    ru.result = Url.RESULT_GOOD
                else:
                    ru.result = Url.RESULT_BAD
            
            ru.save()
            
            for link in outgoing_links:
                ol, created = Url.objects.get_or_create(url=link, run=self._run)
                if c.was_ignored(link):
                    ol.result = Url.RESULT_IGNORED
                    ol.save()
                ru.outgoing_links.add(ol)
            
            ru.save()
            self.log.debug("PageFetch: Url=%d url=%s status=%s, links=%d", ru.id, url, status, len(outgoing_links))
        
        c.on_fetch = _crawl_page_fetch
        c.on_error = self._crawl_page_error
        
        self._run = Run(profile=self._profile, name=run_id)
        self._run.save()
        
        self.log.info("Starting Run: %s (id=%d)", self._run, self._run.id)
        
        d = c.crawl()
        d = d.addCallback(self._crawl_complete)
        d = d.addErrback(self._crawl_error)
        d = d.addBoth(lambda r: reactor.stop())
        
        reactor.run()
        
        self.log.debug("Reactor stopped, run-status=%s", self._run.status)
        return (self._run.status == Run.STATUS_COMPLETE)
    
    def _crawl_page_error(self, url, error):
        ru, c = Url.objects.get_or_create(url=url, run=self._run)
        ru.result = Url.RESULT_ERROR
        ru.save()
        self.log.debug("PageError: Url=%d url=%s error=%s", ru.id, url, error)
    
    def _crawl_complete(self, result):
        self.log.info("Crawl complete")
        self._run.status = Run.STATUS_COMPLETE
        self._run.elapsed_time = (datetime.datetime.now() - self._run.started_at)
        self._run.save()
    
    def _crawl_error(self, result):
        self.log.info("Crawl error")
        self._run.status = Run.STATUS_ERROR
        self._run.elapsed_time = (datetime.datetime.now() - self._run.started_at)
        self._run.save()
        return result
    
if __name__ == '__main__':
    import logging
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print >>sys.stderr, "USAGE: %s PROFILE [RUN_ID]" % sys.argv[0]
        sys.exit(2)
    
    profile = sys.argv[1]
    run_id = (len(sys.argv) > 2) and sys.argv[2] or ''
    
    print >>sys.stderr, "Initializing runner with profile '%s'..." % profile
    r = Runner(profile)
    print >>sys.stderr, "Starting run%s..." % (run_id and (" '%s'" % run_id) or '')
    r.run(run_id)
    sys.exit(0)
