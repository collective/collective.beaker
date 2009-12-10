from zope.interface import Interface
from zope.interface.common.mapping import IMapping
from zope import schema

# Key in request.environ used to store the beaker session
ENVIRON_KEY = 'beaker.session'

#
# Session access
# 

class ISession(IMapping):
    """Adapt the request to ISession to obtain a Beaker session. This
    interface describes the basic Beaker session type.
    """
    
    id = schema.ASCIILine(title=u"SHA-1 key for the session")
    last_accessed = schema.Datetime(title=u"Last access time")
    
    def accessed():
        """Determine if the session has been accessed (and so needs to be
        saved).
        """
    
    def save():
        """Save the session (at the end of the request). This is superfluous
        if, as is the default, the ``auto`` session configuration parameter
        is set to ``True``.
        """
    
    def delete():
        """Mark the session for deletion.
        """
    
    def invalidate():
        """Invalidate the session, giving a fresh one.
        """

class ISessionConfig(IMapping):
    """Beaker session setting, registered as a utility.
    
    These settings are looked up to configure a session. This allows a local
    utility to override settings if required.
    """


#
# Cache manager
# 

class ICacheManager(Interface):
    """A Beaker cache manager.
    
    This is registered as an unnamed utility. You can look this up to perform
    invalidation, for example. However, since the utility is not available
    until after Zope startup and ZCML configuration, you cannot use the
    cache manager instance decorators. Instead, use the @cache_region
    decorator::
    
        from beaker.cache import cache_region
        
        @cache_region('region_name')
        def my_function(self):
            ...
        
    You obviously also need to ensure that the region with the given name is
    configured, usually in ``zope.conf``.
    
    Note that the Beaker cache region concept is inherently global (it relies
    on a module-global variable to keep track of regions), and so there is
    little point in registering a local override or maintaining local settings
    for this..
    """

    def get_cache(name, **kwargs):
        """Obtain a cache by name. Keyword arguments can be used to specify
        caching options, overriding the global options.
        
        See the `Beaker documentation <http://beaker.groovie.org/caching.html>_`
        for further details.
        """
