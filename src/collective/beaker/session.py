from zope.interface import implementer
from zope.component import adapter, queryUtility

from zope.publisher.interfaces.http import IHTTPRequest

from collective.beaker.interfaces import ISession, ISessionConfig, ENVIRON_KEY
from ZPublisher.interfaces import IPubStart, IPubSuccess, IPubFailure

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
                
                cookieOut = sessionInstructions['cookie_out']
                cookieObj = session.cookie[session.key]
                cookieArgs = dict([(k,v) for k,v in cookieObj.items() if v])
                
                if cookieOut:
                    cookieArgs.setdefault('path', session._path)
                    request.response.setCookie(cookieObj.key, cookieObj.value, **cookieArgs)

# Event handlers

@adapter(IPubStart)
def configureSessionOnStart(event):
    initializeSession(event.request)

@adapter(IPubSuccess)
def persistSessionOnSuccess(event):
    closeSession(event.request)

@adapter(IPubFailure)
def persistSessionOnFailure(event):
    if not event.retry:
        closeSession(event.request)
