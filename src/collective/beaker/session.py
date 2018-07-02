from beaker.session import SessionObject
from collective.beaker.interfaces import ISession, ISessionConfig, ENVIRON_KEY
from zope.component import adapter, queryUtility
from zope.interface import implementer
from zope.publisher.interfaces.http import IHTTPRequest
from ZPublisher.interfaces import IPubStart, IPubSuccess, IPubFailure
import urllib


@implementer(ISession)
@adapter(IHTTPRequest)
def ZopeSession(request):
    """Adapter factory from a Zope request to a beaker session
    """
    return request.environ.get(ENVIRON_KEY, None)

# Helper functions


def unquote_cookie_values(environ):
    # Zope "helpfully" urlencodes cookie values,
    # but Beaker needs the unencoded value
    if 'HTTP_COOKIE' in environ:
        cookie = environ['HTTP_COOKIE']

        parts = []
        for part in cookie.split(';'):
            if '=' in part:
                k, v = part.split('=', 1)
                part = '{}={}'.format(k, urllib.unquote(v))
            parts.append(part)
        cookie = '; '.join(parts)

        environ = environ.copy()
        environ['HTTP_COOKIE'] = cookie
    return environ


def initializeSession(request, environ_key='beaker.session'):
    """Create a new session and store it in the request.
    """
    options = queryUtility(ISessionConfig)
    if options is not None:
        environ = unquote_cookie_values(request.environ)
        session = SessionObject(environ, **options)
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
                if sessionInstructions['cookie_out']:
                    cookieObj = session.cookie[session.key]

                    key = cookieObj.key
                    value = session.cookie.value_encode(cookieObj.value)[1]

                    args = dict([(k, v) for k, v in cookieObj.items() if v])
                    args.setdefault('path', session._path)

                    if args.get('httponly'):
                        args.pop('httponly')
                        args['http_only'] = True

                    request.response.setCookie(key, value, **args)

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
