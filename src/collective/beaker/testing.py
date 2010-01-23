import datetime

from zope.interface import implementer
from zope.interface import implements
from zope.component import adapter

from zope.publisher.interfaces import IRequest

from App.config import getConfiguration
from collective.beaker.interfaces import ISession

class BeakerConfigLayer(object):
    """This layer sets up beaker configuration as if it had been present
    in zope.conf. The configuration data is held in self.zconfigData
    """
    
    # Simulated ZConfig data
    zconfigData = {
        'cache.type':           'memory',
        'cache.regions':        'short, long',
        'cache.short.expire':   '3',
        'cache.long.expire':    '10',
        'session.type':         'memory',
        'session.key':          'beaker.session',
        'session.auto':         'off',
    }
    
    @classmethod
    def setUp(self):
        cfg = getConfiguration()
        cfg.product_config = {'beaker': self.zconfigData}

class TestSession(dict):
    """Fake session object that can be used for unit testing
    """
    implements(ISession)
    
    id = 'test-session'
    last_accessed = None
    
    # testing variables
    _accessed = False
    _saved = False
    _deleted = False
    _invalidated = False
    
    def accessed(self):
        return self._accessed
    
    def save(self):
        self._saved = True
    
    def delete(self):
        self._deleted = True
    
    def invalidate(self):
        self._invalidated = True
    
    # make accessed work at least for common cases
    
    def __getitem__(self, key):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        return super(TestSession, self).__getitem__(key)
    
    def __contains__(self, key):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        return super(TestSession, self).__contains__(key)
    
    def get(self, key, default=None):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        return super(TestSession, self).get(key, default)
    
    def __setitem__(self, key, value):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        super(TestSession, self).__setitem__(key, value)
    
    def setdefault(self, key, value):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        return super(TestSession, self).setdefault(key, value)
    
    def __delitem__(self, key):
        self._accessed = True
        self.last_accessed = datetime.datetime.now()
        super(TestSession, self).__delitem__(key)

@implementer(ISession)
@adapter(IRequest)
def testingSession(request):
    return request._environ.setdefault('collective.beaker.testing.session', TestSession())
