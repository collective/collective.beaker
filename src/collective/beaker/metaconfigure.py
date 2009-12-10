from App.config import getConfiguration

from zope.interface import Interface
from beaker.cache import CacheManager

from beaker.util import parse_cache_config_options
from beaker.util import coerce_session_params

from collective.beaker.interfaces import ISessionConfig, ICacheManager

from zope.component.zcml import handler

# Default session options - copied from beaker.middleware
defaultSessionConfig = dict(
        invalidate_corrupt=True,
        type=None, 
        data_dir=None,
        key='beaker.session.id', 
        timeout=None,
        secret=None,
        log_file=None,
    )

class IBeakerConfiguration(Interface):
    """Configuration-less directive which is intended to be used once only.
    It looks up the product configuration in zope.conf and configures global
    components accordingly.
    """

def beakerConfiguration(_context):
    """Read configuration from zope.conf and register components accordingly.
    
    This may result in one or two unnamed utilities:
    
    * ISessionConfig, a dictionary of session parameters from zope.conf
    * ICacheManager, a Beaker CacheManager instance configured from zope.conf
    """
    
    cfg = getConfiguration()
    beakerConfig = cfg.product_config.get('beaker', {})
    
    if beakerConfig:
        cacheConfig = parse_cache_config_options(beakerConfig)
        
        sessionConfig = {}
        for key, value in beakerConfig.items():
            if key.startswith('session.'):
                sessionConfig[key[8:]] = value
            elif key.startswith('beaker.session.'):
                sessionConfig[key[15:]] = value
        coerce_session_params(sessionConfig)
        
        # If we have cache config, register an ICacheManager utility
        if cacheConfig:
            cacheManager = CacheManager(**cacheConfig)
            _context.action(
                discriminator = ('utility', ICacheManager, u""),
                callable = handler,
                args = ('registerUtility', cacheManager, ICacheManager, u""),
                kw = dict(info=cacheConfig),
            )
        
        # If we have session config, register these as an ISessionConfig
        # utility, which will then be looked up when the session factory is
        # invoked.
        if sessionConfig:
            
            # Set defaults for keys not set in the configuration
            sessionConfigWithDefaults = defaultSessionConfig.copy()
            sessionConfigWithDefaults.update(sessionConfig)
            
            _context.action(
                discriminator = ('utility', ISessionConfig, u""),
                callable = handler,
                args = ('registerUtility', sessionConfigWithDefaults, ISessionConfig, u""),
                kw = dict(info=sessionConfig),
            )
