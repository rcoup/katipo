import urlparse
import datetime
import urllib

from django.db import models
from django.core.urlresolvers import reverse

from utils.fields import PythonField, TimedeltaField

class Profile(models.Model):
    name = models.CharField(max_length=200, unique=True)
    settings = PythonField(blank=True)
    
    def __unicode__(self):
        return unicode(self.name)
    
    @models.permalink
    def get_absolute_url(self):
        return ('katipo-profile-detail', [str(self.id)])
    
    @property
    def start_urls(self):
        return self.get_settings_module().get('START_URLS', ())
    
    @property
    def ignore_url_match(self):
        return self.get_settings_module().get('IGNORE_URL_MATCH', ())
    
    @property
    def extra_hosts(self):
        return self.get_settings_module().get('EXTRA_HOSTS', ())
    
    @property
    def test_externals(self):
        return self.get_settings_module().get('TEST_EXTERNALS', True)
    
    @property
    def parse_content_types(self):
        return self.get_settings_module().get('PARSE_CONTENT_TYPES', (r'^text/', r'^application/xhtml+xml$'))
    
    @property
    def expected_errors(self):
        return self.get_settings_module().get('EXPECTED_ERRORS', ())
    
    def get_run_latest(self):
        try:
            return self.runs.all()[0]
        except IndexError, e:
            return None
    
    def get_run_previous(self):
        try:
            return self.runs.all()[1]
        except IndexError, e:
            return None

class Run(models.Model):
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_ABORTED = 'ABORTED'
    
    CHOICES_STATUS = (
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_ABORTED, 'Aborted'),
    )
    
    name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=CHOICES_STATUS, default=STATUS_RUNNING)
    started_at = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey(Profile, related_name='runs')
    elapsed_time = TimedeltaField(null=True)
    
    class Meta:
        ordering = ('-started_at',)
    
    def __unicode__(self):
        return unicode(self.name) or u"%s @ %s (#%d)" % (self.profile, self.started_at, self.id)
    
    @models.permalink
    def get_absolute_url(self):
        return ('katipo-run-detail', [str(self.id)])
    
    @property
    def count_crawled(self):
        return self.urls.exclude(result='').count()
    @property
    def count_ignored(self):
        return self.urls.filter(result=Url.RESULT_IGNORED).count()
    @property
    def count_not_crawled(self):
        return self.urls.filter(result='').count()
    @property
    def count_internal(self):
        return self.urls.filter(is_internal=True).exclude(result='').count()
    @property
    def count_external(self):
        return self.urls.filter(is_internal=False).exclude(result='').count()
    @property
    def count_good(self):
        return self.urls.filter(result=Url.RESULT_GOOD).count()
    @property
    def count_bad(self):
        return self.urls.filter(result=Url.RESULT_BAD).count()
    @property
    def count_errors(self):
        return self.urls.filter(result=Url.RESULT_ERROR).count()
    @property
    def count_timeouts(self):
        return self.urls.filter(result=Url.RESULT_TIMEOUT).count()
    
    def _percent(self, quantity):
        # handle div/zero
        return 100.0 * quantity / self.count_crawled if self.count_crawled else 0.0
    
    @property
    def count_internal_pc(self):
        return self._percent(self.count_internal)
    @property
    def count_external_pc(self):
        return self._percent(self.count_external)
    @property
    def count_good_pc(self):
        return self._percent(self.count_good)
    @property
    def count_bad_pc(self):
        return self._percent(self.count_bad)
    @property
    def count_errors_pc(self):
        return self._percent(self.count_errors)
    @property
    def count_timeouts_pc(self):
        return self._percent(self.count_timeouts)
    
    def get_good(self):
        return self.urls.filter(result=Url.RESULT_GOOD)
    def get_bad(self):
        return self.urls.filter(result=Url.RESULT_BAD)
    def get_errors(self):
        return self.urls.filter(result=Url.RESULT_ERROR)
    def get_timeouts(self):
        return self.urls.filter(result=Url.RESULT_TIMEOUT)
    def get_ignored(self):
        return self.urls.filter(result=Url.RESULT_IGNORED)
    def get_not_crawled(self):
        return self.urls.filter(result='')
    def get_all_errors(self):
        return self.urls.exclude(result__in=(Url.RESULT_GOOD, Url.RESULT_IGNORED, '')).order_by('result', 'status_code', 'url')

class UrlManager(models.Manager):
    def distinct_urls(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT url FROM katipo_url ORDER BY url")
        return tuple([row[0] for row in cursor.fetchall()])
        
    def search(self, url_string):
        """ 
        Return newest instances of each URL found by a search:
            1. Exact matches (if include_exact)
            2. Starts-with (case sensitive)
            3. Starts-with (case-insensitive)
            4. Contains (case-sensitive)
            5. Contains (case-insensitive)
        
        Result is formatted as a dictionary:
        {
            'exact' : <exact-match Url or None>,
            'inexact': [<ordered list of inexact matches>],
        }
        """
        #FIXME: Make it actually do the above
        
        exact = Url.objects.filter(url=url_string)[:1]
        url_exact = len(exact) and exact[0] or None 
        
        r = {
            'exact': url_exact,
            'inexact': (),
        }
        return r
        

class Url(models.Model):
    RESULT_GOOD = 'GOOD'
    RESULT_BAD = 'BAD'
    RESULT_ERROR = 'ERROR'
    RESULT_TIMEOUT = 'TIMEOUT'
    RESULT_IGNORED = 'IGNORED'
    
    CHOICES_RESULT = (
        (RESULT_GOOD, 'Good (expected status)'),
        (RESULT_BAD, 'Bad (unexpected status)'),
        (RESULT_ERROR, 'Error'),
        (RESULT_TIMEOUT, 'Timeout'),
        (RESULT_IGNORED, 'Ignored'),
    )
    
    objects = UrlManager()
    
    run = models.ForeignKey(Run, related_name='urls')
    url = models.CharField(max_length=4096, db_index=True)
    
    result = models.CharField(max_length=10, blank=True, choices=CHOICES_RESULT, db_index=True)
    status_code = models.IntegerField(null=True, db_index=True)
    elapsed_time = TimedeltaField(null=True, db_index=True)
    is_internal = models.BooleanField(default=False, db_index=True)
    
    outgoing_links = models.ManyToManyField('self', symmetrical=False, related_name='incoming_links', blank=True)
    
    class Meta:
        unique_together = (('run', 'url'),)
        ordering = ('url', 'run',)
    
    def __unicode__(self):
        return u"%s - %s" % (self.url, self.result or 'NOT_CRAWLED')
    
    def get_absolute_url(self):
        u = reverse('katipo-url-detail', args=(self.run_id,))
        u += "?" 
        u += urllib.urlencode({'u':self.url})
        return u
    
    def get_domain(self, include_scheme=True):
        up = self.url_parts
        if include_scheme:
            return urlparse.urlunsplit((up.scheme, up.netloc, None, None, None))
        else:
            return up.netloc
    
    def get_all_runs(self):
        return Url.objects.filter(url=self.url)
    
    @property
    def url_parts(self):
        return urlparse.urlsplit(self.url)

    