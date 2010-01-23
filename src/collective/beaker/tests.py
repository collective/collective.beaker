
import time
import unittest

import zope.component.testing
from zope.component import provideAdapter

from zope.publisher.browser import TestRequest

import collective.testcaselayer.ptc
import collective.beaker

from Products.PloneTestCase import ptc
from Products.Five.testbrowser import Browser
from Products.Five.browser import BrowserView
from Products.Five import fiveconfigure
from Products.Five import zcml

from zope.component import getUtility

from collective.beaker.interfaces import ISession
from collective.beaker.interfaces import ICacheManager
from collective.beaker.interfaces import ISessionConfig

from beaker.cache import cache_region

from collective.beaker.testing import BeakerConfigLayer
from collective.beaker.testing import testingSession

ptc.setupPloneSite()

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

class CollectiveBeakerLayer(collective.testcaselayer.ptc.BasePTCLayer):
    
    def afterSetUp(self):
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

# Make sure we load the beaker config layer first, otherwise we may not have
# configuration by the time the beaker data is loaded
Layer = CollectiveBeakerLayer([BeakerConfigLayer, collective.testcaselayer.ptc.ptc_layer])

class TestSession(ptc.FunctionalTestCase):
    
    layer = Layer
    
    def afterSetUp(self):
        self.browser = Browser()
        self.browser.handleErrors = False
        self.url = self.portal.absolute_url() + '/@@session-test?'
    
    def test_create_persist(self):
        
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

    def test_create_persist_signed_cookie(self):
        
        config = getUtility(ISessionConfig)
        config['secret'] = 'password'
        
        try:
            
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
        
        finally:
            del config['secret']
    
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

class TestTestSession(unittest.TestCase):
    
    def tearDown(self):
        zope.component.testing.tearDown()
    
    def test_test_session_not_registered(self):
        request = TestRequest()
        self.assertEquals(None, ISession(request, None))
    
    def test_test_session_unique_to_request(self):
        provideAdapter(testingSession)
        
        request1 = TestRequest()
        request2 = TestRequest()
        
        session1 = ISession(request1)
        session2 = ISession(request2)
        
        session1['foo'] = 'bar'
        self.assertEquals('bar', session1['foo'])
        self.failIf('foo' in session2)
    
    def test_saved(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(False, session._saved)
        session.save()
        self.assertEquals(True, session._saved)
    
    def test_deleted(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(False, session._deleted)
        session.delete()
        self.assertEquals(True, session._deleted)
    
    def test_invalidated(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(False, session._invalidated)
        session.invalidate()
        self.assertEquals(True, session._invalidated)
    
    def test_accessed_setitem(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(None, session.last_accessed)
        self.assertEquals(False, session.accessed())
        
        session['foo'] = 'bar'
        
        self.failIf(session.last_accessed is None)
        self.assertEquals(True  , session.accessed())
    
    def test_accessed_get(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(None, session.last_accessed)
        self.assertEquals(False, session.accessed())
        
        session.get('foo')
        
        self.failIf(session.last_accessed is None)
        self.assertEquals(True  , session.accessed())
    
    def test_accessed_contains(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(None, session.last_accessed)
        self.assertEquals(False, session.accessed())
        
        'foo' in session
        
        self.failIf(session.last_accessed is None)
        self.assertEquals(True  , session.accessed())
    
    def test_accessed_setdefault(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        
        self.assertEquals(None, session.last_accessed)
        self.assertEquals(False, session.accessed())
        
        session.setdefault('foo', 'bar')
        
        self.failIf(session.last_accessed is None)
        self.assertEquals(True  , session.accessed())
    
    def test_get_del(self):
        provideAdapter(testingSession)
        
        request = TestRequest()
        session = ISession(request)
        session['foo'] = 'bar'
        
        self.assertEquals('bar', session['foo'])
        del session['foo']
        self.failIf('foo' in session)
        
        self.failIf(session.last_accessed is None)
        self.assertEquals(True  , session.accessed())

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
