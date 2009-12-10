import time
import unittest

import collective.testcaselayer.ptc
import collective.beaker

from Products.PloneTestCase import ptc
from Products.Five.testbrowser import Browser
from Products.Five.browser import BrowserView
from Products.Five import fiveconfigure
from Products.Five import zcml

from App.config import getConfiguration

from zope.component import getUtility
from collective.beaker.interfaces import ISession, ICacheManager

from beaker.cache import cache_region

ptc.setupPloneSite()

# Simulates data from ZConfig.
config = {
    'cache.type':           'memory',
    'cache.regions':        'short, long',
    'cache.short.expire':   '3',
    'cache.long.expire':    '10',
    'session.type':         'memory',
    'session.key':          'beaker.session',
    'session.auto':         'off',
}

# Views used to test session behavior

class SessionTestView(BrowserView):
    
    def __call__(self):
        session = ISession(self.request)
        if 'reset' in self.request:
            session['testCounter'] = 0
            session.save()
        if 'increment' in self.request:
            session['testCounter'] += 1
            session.save()
        if 'invalidate' in self.request:
            session.invalidate()
        if 'delete' in self.request:
            session.delete()
        return str(session.get('testCounter', -1))

# Module scope method used to test region behavior (note that region is not
# yet defined)

@cache_region('short')
def cachedShort():
    return time.time()

class BeakerLayer(collective.testcaselayer.ptc.BasePTCLayer):

    def afterSetUp(self):
        # Simulate ZConfig parsing <product-config beaker />
        cfg = getConfiguration()
        cfg.product_config = {'beaker': config}
        
        fiveconfigure.debug_mode = True
        
        zcml.load_config('configure.zcml', package=collective.beaker)
        zcml.load_string("""\
        <configure package="collective.beaker" xmlns="http://namespaces.zope.org/browser">
            <view
                name="session-test"
                for="*"
                class=".tests.SessionTestView"
                permission="zope2.View"
                />
        </configure>""")
        fiveconfigure.debug_mode = False

Layer = BeakerLayer([collective.testcaselayer.ptc.ptc_layer])

class TestSession(ptc.FunctionalTestCase):
    
    layer = Layer
    
    def afterSetUp(self):
        self.browser = Browser()
        self.browser.handleErrors = False
        self.url = self.portal.absolute_url() + '/@@session-test?'
    
    def test_create_persist(self):
        
        self.fail
        
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)
        
        self.browser.open(self.url + 'reset')
        self.assertEquals('0', self.browser.contents)
        
        self.browser.open(self.url + 'increment')
        self.assertEquals('1', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('1', self.browser.contents)
        
        self.browser.open(self.url + 'increment')
        self.assertEquals('2', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('2', self.browser.contents)
    
    def test_invalidate(self):
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)
        
        self.browser.open(self.url + 'reset')
        self.assertEquals('0', self.browser.contents)
        
        self.browser.open(self.url + 'increment')
        self.assertEquals('1', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('1', self.browser.contents)
        
        self.browser.open(self.url + 'invalidate')
        self.assertEquals('-1', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)
        
        self.browser.open(self.url + 'reset')
        self.assertEquals('0', self.browser.contents)
        
        self.browser.open(self.url + 'increment')
        self.assertEquals('1', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('1', self.browser.contents)
    
    def test_delete(self):
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)
 
        self.browser.open(self.url + 'reset')
        self.assertEquals('0', self.browser.contents)
        
        self.browser.open(self.url + 'increment')
        self.assertEquals('1', self.browser.contents)
        self.browser.open(self.url)
        self.assertEquals('1', self.browser.contents)
        
        self.browser.open(self.url + 'delete')
        self.assertEquals('-1', self.browser.contents)
        
        # XXX: We should test that the cookie has expired now, except
        # that zope.testbrowser does not correctly expire cookies :(
        
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)
        
        self.browser.open(self.url)
        self.assertEquals('-1', self.browser.contents)

class TestCacheRegion(ptc.PloneTestCase):
    
    layer = Layer
    
    def test_region_cache(self):
        t1 = cachedShort()
        time.sleep(1)
        
        self.assertEquals(t1, cachedShort())
        
        # let cache expire
        time.sleep(3)
        self.assertNotEquals(t1, cachedShort())
    
    def test_cache_lookup(self):
        
        cacheManager = getUtility(ICacheManager)
        cache = cacheManager.get_cache('foo', expire=3)
        
        counter = [0]
        
        def increment():
            counter[0] += 1
            return counter[0]
        
        v1 = cache.get(key='bar', createfunc=increment)
        v2 = cache.get(key='bar', createfunc=increment)
        
        time.sleep(4)
        
        v3 = cache.get(key='bar', createfunc=increment)
        
        self.assertEquals(1, v1)
        self.assertEquals(1, v2)
        self.assertEquals(2, v3)
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
