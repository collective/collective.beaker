from zope.interface import implementer
from zope.component import adapter, queryUtility

from zope.publisher.interfaces.http import IHTTPRequest

from collective.beaker.interfaces import ISession, ISessionConfig, ENVIRON_KEY
from ZPublisher.interfaces import IPubStart, IPubBeforeCommit, IPubBeforeAbort

from beaker.session import SessionObject

@implementer(ISession)
@adapter(IHTTPRequest)
def ZopeSession(request):
    """Adapter factory from a Zope request to a beaker session
    """
    return request.environ.get(ENVIRON_KEY, None)

# Helper functions

def initializeSession(request, environ_key='beaker.session'):
    """Create a new session and store it in the request.
    """
    options = queryUtility(ISessionConfig)
    if options is not None:
        session = SessionObject(request.environ, **options)
        request.environ[ENVIRON_KEY] = session

def closeSession(request):
    """Close the session, and, if necessary, set any required cookies
    """
    session = ISession(request, None)
    if session is not None:
        if session.accessed():
            session.persist()
            sessionInstructions = session.request
            if sessionInstructions.get('set_cookie', False):
                
                # XXX: This approach is what Beaker does itself, and it seems
                # to work best TTW (no superfluous/stale cookies on delete).
                # It breaks the functional tests, though                
                # cookie = sessionInstructions['cookie_out']
                # if cookie:
                #     request.response.addHeader('Set-Cookie', cookie)
                
                # XXX: This works in tests, but sometimes seems to leave
                # stale cookies TTW when sessions are deleted.
                
                cookie = session.cookie[session.key]
                if cookie:
                    cookieArgs = dict([(k,v) for k,v in cookie.items() if v])
                    request.response.setCookie(cookie.key, cookie.value, **cookieArgs)

# Event handlers

@adapter(IPubStart)
def configureSessionOnStart(event):
    initializeSession(event.request)

@adapter(IPubBeforeCommit)
def persistSessionOnSuccess(event):
    closeSession(event.request)

@adapter(IPubBeforeAbort)
def persistSessionOnFailure(event):
    if not event.retry:
        closeSession(event.request)
