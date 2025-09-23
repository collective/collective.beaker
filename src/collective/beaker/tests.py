from beaker.cache import cache_region
from collective.beaker.interfaces import ICacheManager
from collective.beaker.interfaces import ISession
from collective.beaker.interfaces import ISessionConfig
from collective.beaker.testing import BEAKER_FUNCTIONAL_TESTING
from collective.beaker.testing import BEAKER_INTEGRATION_TESTING
from collective.beaker.testing import testingSession
from plone.testing.z2 import Browser
from zope.component import getUtility
from zope.component import provideAdapter
from zope.publisher.browser import BrowserView
from zope.publisher.browser import TestRequest

import time
import unittest
import zope.component.testing


# Views used to test session behavior


class SessionTestView(BrowserView):
    def __call__(self):
        session = ISession(self.request)
        if "reset" in self.request:
            session["testCounter"] = 0
            session.save()
        if "increment" in self.request:
            session["testCounter"] += 1
            session.save()
        if "invalidate" in self.request:
            session.invalidate()
        if "delete" in self.request:
            session.delete()
        return str(session.get("testCounter", -1))


# Module scope method used to test region behavior (note that region is not
# yet defined)


@cache_region("short")
def cachedShort():
    return time.time()


class TestSession(unittest.TestCase):

    layer = BEAKER_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.browser = Browser(self.app)
        self.browser.handleErrors = False
        self.url = self.portal.absolute_url() + "/@@session-test?"

    def test_create_persist(self):
        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)

        self.browser.open(self.url + "reset")
        self.assertEqual("0", self.browser.contents)

        self.browser.open(self.url + "increment")
        self.assertEqual("1", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("1", self.browser.contents)

        self.browser.open(self.url + "increment")
        self.assertEqual("2", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("2", self.browser.contents)

    def test_create_persist_signed_cookie(self):
        config = getUtility(ISessionConfig)
        config["secret"] = "password"
        try:
            self.browser.open(self.url)
            self.assertEqual("-1", self.browser.contents)

            self.browser.open(self.url + "reset")
            self.assertEqual("0", self.browser.contents)

            self.browser.open(self.url + "increment")
            self.assertEqual("1", self.browser.contents)
            self.browser.open(self.url)
            self.assertEqual("1", self.browser.contents)

            self.browser.open(self.url + "increment")
            self.assertEqual("2", self.browser.contents)
            self.browser.open(self.url)
            self.assertEqual("2", self.browser.contents)
        finally:
            del config["secret"]

    def test_invalidate(self):
        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)

        self.browser.open(self.url + "reset")
        self.assertEqual("0", self.browser.contents)

        self.browser.open(self.url + "increment")
        self.assertEqual("1", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("1", self.browser.contents)

        self.browser.open(self.url + "invalidate")
        self.assertEqual("-1", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)

        self.browser.open(self.url + "reset")
        self.assertEqual("0", self.browser.contents)

        self.browser.open(self.url + "increment")
        self.assertEqual("1", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("1", self.browser.contents)

    def test_delete(self):
        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)

        self.browser.open(self.url + "reset")
        self.assertEqual("0", self.browser.contents)

        self.browser.open(self.url + "increment")
        self.assertEqual("1", self.browser.contents)
        self.browser.open(self.url)
        self.assertEqual("1", self.browser.contents)

        self.browser.open(self.url + "delete")
        self.assertEqual("-1", self.browser.contents)

        # XXX: We should test that the cookie has expired now, except
        # that zope.testbrowser does not correctly expire cookies :(

        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)

        self.browser.open(self.url)
        self.assertEqual("-1", self.browser.contents)


class TestCacheRegion(unittest.TestCase):

    layer = BEAKER_INTEGRATION_TESTING

    def test_region_cache(self):
        t1 = cachedShort()
        time.sleep(1)
        self.assertEqual(t1, cachedShort())
        # let cache expire
        time.sleep(3)
        self.assertNotEqual(t1, cachedShort())

    def test_cache_lookup(self):
        cacheManager = getUtility(ICacheManager)
        cache = cacheManager.get_cache("foo", expire=3)

        counter = [0]

        def increment():
            counter[0] += 1
            return counter[0]

        v1 = cache.get(key="bar", createfunc=increment)
        v2 = cache.get(key="bar", createfunc=increment)

        time.sleep(4)

        v3 = cache.get(key="bar", createfunc=increment)

        self.assertEqual(1, v1)
        self.assertEqual(1, v2)
        self.assertEqual(2, v3)


class TestTestSession(unittest.TestCase):
    def tearDown(self):
        zope.component.testing.tearDown()

    def test_test_session_not_registered(self):
        request = TestRequest()
        self.assertEqual(None, ISession(request, None))

    def test_test_session_unique_to_request(self):
        provideAdapter(testingSession)

        request1 = TestRequest()
        request2 = TestRequest()

        session1 = ISession(request1)
        session2 = ISession(request2)

        session1["foo"] = "bar"
        self.assertEqual("bar", session1["foo"])
        self.assertFalse("foo" in session2)

    def test_saved(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(False, session._saved)
        session.save()
        self.assertEqual(True, session._saved)

    def test_deleted(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(False, session._deleted)
        session.delete()
        self.assertEqual(True, session._deleted)

    def test_invalidated(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(False, session._invalidated)
        session.invalidate()
        self.assertEqual(True, session._invalidated)

    def test_accessed_setitem(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(None, session.last_accessed)
        self.assertEqual(False, session.accessed())

        session["foo"] = "bar"

        self.assertFalse(session.last_accessed is None)
        self.assertEqual(True, session.accessed())

    def test_accessed_get(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(None, session.last_accessed)
        self.assertEqual(False, session.accessed())

        session.get("foo")

        self.assertFalse(session.last_accessed is None)
        self.assertEqual(True, session.accessed())

    def test_accessed_contains(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(None, session.last_accessed)
        self.assertEqual(False, session.accessed())

        "foo" in session

        self.assertFalse(session.last_accessed is None)
        self.assertEqual(True, session.accessed())

    def test_accessed_setdefault(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)

        self.assertEqual(None, session.last_accessed)
        self.assertEqual(False, session.accessed())

        session.setdefault("foo", "bar")

        self.assertFalse(session.last_accessed is None)
        self.assertEqual(True, session.accessed())

    def test_get_del(self):
        provideAdapter(testingSession)

        request = TestRequest()
        session = ISession(request)
        session["foo"] = "bar"

        self.assertEqual("bar", session["foo"])
        del session["foo"]
        self.assertFalse("foo" in session)

        self.assertFalse(session.last_accessed is None)
        self.assertEqual(True, session.accessed())
