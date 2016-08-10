collective.beaker - Beaker integration for Zope 2 and Plone.
============================================================

This package provides a means to configure the `Beaker
<http://beaker.groovie.org>`_ session management and caching framework for
use within a Zope 2 (and Plone) environment.

Ordinarily, Beaker is configured using WSGI middleware. However, Zope 2 does
not (yet) run WSGI by default (unless you use ``repoze.zope2``). This package
provides an alternative configuration syntax, based in zope.conf.

Installation
------------

To use this package, you need to install it. Typically, you would do this
via the ``install_requires`` line in your own package's ``setup.py``::

    install_requires=[
          ...
          'collective.beaker',
      ],

You can also install it using the ``eggs`` line in buildout.cfg, e.g.::

    [instance]
    ...
    eggs =
        ...
        collective.beaker

If you are on Zope 2.10 (e.g. for Plone 3), you will also need to install the
`ZPublisherEventsBackport
<http://pypi.python.org/pypi/ZPublisherEventsBackport>`_ package. You can
get that as a dependency by depending in the ``[Zope2.10]`` extra, e.g.::

    [instance]
    ...
    eggs =
        ...
        collective.beaker [Zope2.10]

If you are in Zope 2.12 or later, the relevant events are included by default,
and you should *not* depend on ``ZPublisherEventsBackport`` or the
``[Zope2.10]`` extra.

Configuring Beaker
------------------

To configure Beaker, add a section to your ``zope.conf`` like this::

    <product-config beaker>
        cache.type              file
        cache.data_dir          /tmp/cache/data
        cache.lock_dir          /tmp/cache/lock
        cache.regions           short, long
        cache.short.expire      60
        cache.long.expire       3600
        
        session.type            file
        session.data_dir        /tmp/sessions/data
        session.lock_dir        /tmp/sessions/lock
        session.key             beaker.session
        session.secret          secret
    </product-config>

If you are using buildout and ``plone.recipe.zope2instance`` to generate your
``zope.conf``, you can use the following option::

    [instance]
    ...
    zope-conf-additional =
        <product-config beaker>
            cache.type              file
            cache.data_dir          ${buildout:directory}/var/cache/data
            cache.lock_dir          ${buildout:directory}/var/cache/lock
            cache.regions           short, long
            cache.short.expire      60
            cache.long.expire       3600
        
            session.type            file
            session.data_dir        ${buildout:directory}/var/sessions/data
            session.lock_dir        ${buildout:directory}/var/sessions/lock
            session.key             beaker.session
            session.secret          secret
        </product-config>

Here, we have also used a buildout substitution to put the cache and session
directories inside the buildout directory.

You also need to load the configuration for the ``collective.beaker`` package.
This can be done with a ZCML line like this::

    <include package="collective.beaker" />

This could be in your own ``configure.zcml``, or in a ZCML slug. If you are
using buildout and ``plone.recipe.zope2instance``, you can install a slug
by adding a ``zcml`` line like::

    [instance]
    ...
    zcml =
        collective.beaker

The settings within the ``<product-config beaker>`` section are passed
directly to Beaker. See the `Beaker configuration documentation
<http://beaker.groovie.org/configuration.html>`_ for more details about the
available options.

Please note that:

* All cache settings must be prefixed with ``cache.``
* All session settings must be prefixed with ``session.``

For the session settings, the following defaults apply:

* ``invalidate_corrupt=True``, so corrupt sessions are invalidated
* ``type=None`` and ``data_dir=None``, thus defaulting to an in-memory
  session
* ``key=beaker.session.id`` - this is the cookie key
* ``timeout=None``, so sessions don't time out
* ``secret=None``, so session cookies are not encrypted
* ``log_file=None``, so there is no logging

Using sessions
--------------

To obtain a Beaker session from a request, use the following pattern::

    >>> from collective.beaker.interfaces import ISession
    >>> session = ISession(request)

See the `Beaker session documentation
<http://beaker.groovie.org/sessions.html>`_ for details on the resultant
session object. You can more or less treat it as a dictionary with string
keys::

    >>> session['username'] = currentUserName

If you modify the session, you need to manually save it::

    >>> session.save()

Alternatively, you can set the ``session.auto`` configuration key to ``on``,
and sessions will be automatically saved on each request.

If you want to delete the session, use::

    >>> session.delete()

Note that Beaker does not automatically expire/remove sessions, so you may
need to do this yourself.

If you want to invalidate the session and create a new one, use::

    >>> session.invalidate()

Note that the session is configured when each request is begun, based on the
session settings read from ``zope.conf``. It is possible to override these
by registering a utility providing ``ISessionConfig`` from this package. The
utility must implement the dict API (you can use a regular dict, or a
persistent mapping object, for example). This allows, for example, a site-
local utility to provide per-site session data.

Using caching
-------------

The Beaker documentation illustrates how to create a cache manager as a 
global variable. The ``CacheManager`` instance provides decorators and
functions to use the cache. You can still use this pattern, but this will
not use any of the configuration managed by ``collective.beaker`` in zope.conf

You can, however, use cache regions, as well as the explicit caching API. At
runtime (but *not* in module scope) you can obtain a Beaker ``CacheManager``
that is configured as per ``zope.conf`` like so::

    >>> from zope.component import getUtility
    >>> from collective.beaker.interfaces import ICacheManager
    
    >>> cacheManager = getUtility(ICacheManager)

You can now use this programmatically as per the Beaker documentation, e.g.::

    >>> myCache = cacheManager.get_cache('mynamespace', expire=1800)

Refer to the `Beaker caching documentation
<http://beaker.groovie.org/caching.html>`_ for details.

You can also use caching region decorators, e.g. with::

    >>> from beaker.cache import cache_region
    >>> @cache_region('short')
    ... def my_function():
    ...     ...

Provided that the 'short' region is configured (as in the ``zope.conf``
example above), this will lazily look up the region settings and use those
for caching.

To invalidate the cache, you could call::

    >>> from beaker.cache import region_invalidate
    >>> region_invalidate(my_function, 'short')

Again, refer to the Beaker documentation for details.

Testing
-------

If you are writing integration tests for code that uses beaker sessions or
caches, you need to ensure that beaker is configured before you call the
relevant code. Otherwise, you are liable to get component lookup errors
on ``ISessionConfig`` or ``ICacheManager`` layers. This is because integration
tests written with ``ZopeTestCase``/``PloneTestCase`` do not read your
``zope.conf`` and so the ``collective.beaker`` configuration code does not
have any configuration data when it is loaded.

You can deal with this in one of two ways:

* Register your own ``ISessionConfig`` and/or ``ICacheManager`` utilities.
  See ``interfaces.py`` for details.
* Provide "fake" ZConfig settings before ZCML processing takes place.

You can use the test layer in ``collective.beaker.testing.BeakerConfigLayer``
to do the latter. You need to make sure that this layer is mixed in before
any layer that executes ZCML processing. For example::

    from colective.beaker.testing import BeakerConfigLayer
    from Products.PloneTestCase.layer import PloneSiteLayer
    from Products.PloneTestCase.ptc import PloneTestCase
    
    class MyLayer(BeakerConfigLayer, PloneSiteLayer):
        pass
    
    class TestCase(PloneTestCase):
        
        layer = MyLayer
    
You can of course add your own ``setUp`` and ``tearDown`` methods to the
layer. The important thing is that the ``BeakerConfigLayer`` comes before
the ``PloneSiteLayer``, which will configure the site.

This setup will use default settings (see ``testing.py`` for the exact
values), but you can manipulate these on a per-setting basis. For example::

    from zope.component import getUtility
    from collective.beaker.interfaces import ISessionConfig
    
    config = getUtility(ISessionConfig)
    config['secret'] = 'password'

Bear in mind that this is normally a global utility, so any changes will
cross test boundaries unless you also tear down your settings properly. Thus,
it is probably more appropriate to do this setup in a layer than in an
individual test.

When writing tests that use Beaker sessions, if you are not performing
functional testing using something like ``zope.testbrowser``, you may also
need to simulate the request start/end events that ``collective.beaker``
listens to in order to configure the session.

For example::

    from collective.beaker.session import initializeSession, closeSession
    
    ...
    
    class TestCase(PloneTestCase):
        
        layer = MyLayer
        
        def test_something(self):
            request = self.app.REQUEST
            initializeSession(request)
            
            # perform your test here
            
            closeSession(request)

In a unit test, it is probably easier to just provide a mock ``ISession``
adapter for the request. There is a mock session implementation in this
package which can help you with that::
    
    import unittest
    import zope.component.testing
    
    from zope.component import provideAdapter
    from collective.beaker.testing import testingSession
    
    from collective.beaker.interfaces import ISession
    from zope.publisher.browser import TestRequest
    
    
    class MyUnitTestCase(unittest.TestCase):
        
        def setUp(self):
            provideAdapter(testingSession)
            ...
        
        def tearDown(self):
            zope.component.testing.tearDown()
        
        def test_something(self):
            request = TestRequest()
            session = ISession(request)
            ...

Like the "real" session, the test session is tied to the request, so you
should get the same object back each time you look up the adapter on the
request. You can also check the following properties to see how the session
has been used:

* ``_saved`` is True if ``save()`` has been called once.
* ``_invalidated`` is True if ``invalidate()`` has been called once.
* ``_deleted`` is True if ``delete()`` has been called once.

Finally, ``accessed()`` will return True and the ``last_accessed`` attribute
will be set to the current date/time when common dictionary operations are
used.
