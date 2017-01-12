import logging
import urlparse

from decimal import Decimal
from zope.interface import implements
from twisted.web import server, resource
from twisted.internet import defer
from twisted.python.failure import Failure

from txjsonrpc import jsonrpclib
from lbrynet.core.Error import InvalidAuthenticationToken, InvalidHeaderError
from lbrynet import conf
from lbrynet.lbrynet_daemon.auth.util import APIKey, get_auth_message
from lbrynet.lbrynet_daemon.auth.client import LBRY_SECRET

log = logging.getLogger(__name__)

EMPTY_PARAMS = [{}]


def default_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)


class JSONRPCException(Exception):
    def __init__(self, err, code):
        self.faultCode = code
        self.err = err

    @property
    def faultString(self):
        return self.err.getTraceback()


class AuthorizedBase(object):
    def __init__(self):
        self.authorized_functions = []
        self.callable_methods = {}

        for methodname in dir(self):
            if methodname.startswith("jsonrpc_"):
                method = getattr(self, methodname)
                self.callable_methods.update({methodname.split("jsonrpc_")[1]: method})
                if hasattr(method, '_auth_required'):
                    self.authorized_functions.append(methodname.split("jsonrpc_")[1])

    @staticmethod
    def auth_required(f):
        f._auth_required = True
        return f


class AuthJSONRPCServer(AuthorizedBase):
    """Authorized JSONRPC server used as the base class for the LBRY API

    API methods are named with a leading "jsonrpc_"

    Decorators:

        @AuthJSONRPCServer.auth_required: this requires the client
            include a valid hmac authentication token in their request

    Attributes:
        allowed_during_startup (list): list of api methods that are
            callable before the server has finished startup

        sessions (dict): dictionary of active session_id:
            lbrynet.lbrynet_daemon.auth.util.APIKey values

        authorized_functions (list): list of api methods that require authentication

        callable_methods (dict): dictionary of api_callable_name: method values

    """
    implements(resource.IResource)

    isLeaf = True
    OK = 200
    UNAUTHORIZED = 401
    # TODO: codes should follow jsonrpc spec: http://www.jsonrpc.org/specification#error_object
    NOT_FOUND = 8001
    FAILURE = 8002

    def __init__(self, use_authentication=None):
        AuthorizedBase.__init__(self)
        self._use_authentication = (
            use_authentication if use_authentication is not None else conf.settings.use_auth_http)
        self.announced_startup = False
        self.allowed_during_startup = []
        self.sessions = {}

    def setup(self):
        return NotImplementedError()

    def _render_error(self, failure, request, id_,
                      version=jsonrpclib.VERSION_2, response_code=FAILURE):
        err = JSONRPCException(Failure(failure), response_code)
        fault = jsonrpclib.dumps(err, id=id_, version=version)
        self._set_headers(request, fault)
        if response_code != AuthJSONRPCServer.FAILURE:
            request.setResponseCode(response_code)
        request.write(fault)
        request.finish()

    def render(self, request):
        notify_finish = request.notifyFinish()
        assert self._check_headers(request), InvalidHeaderError
        session = request.getSession()
        session_id = session.uid

        if self._use_authentication:
            # if this is a new session, send a new secret and set the expiration
            # otherwise, session.touch()
            if self._initialize_session(session_id):
                def expire_session():
                    self._unregister_user_session(session_id)

                session.startCheckingExpiration()
                session.notifyOnExpire(expire_session)
                message = "OK"
                request.setResponseCode(self.OK)
                self._set_headers(request, message, True)
                self._render_message(request, message)
                return server.NOT_DONE_YET
            else:
                session.touch()

        request.content.seek(0, 0)
        content = request.content.read()
        try:
            parsed = jsonrpclib.loads(content)
        except ValueError as err:
            log.warning("Unable to decode request json")
            self._render_error(err, request, None)
            return server.NOT_DONE_YET

        function_name = parsed.get('method')
        args = parsed.get('params')
        id_ = parsed.get('id')
        token = parsed.pop('hmac', None)
        version = self._get_jsonrpc_version(parsed.get('jsonrpc'), id_)

        reply_with_next_secret = False
        if self._use_authentication:
            if function_name in self.authorized_functions:
                try:
                    self._verify_token(session_id, parsed, token)
                except InvalidAuthenticationToken as err:
                    log.warning("API validation failed")
                    self._render_error(
                        err, request, id_, version=version,
                        response_code=AuthJSONRPCServer.UNAUTHORIZED)
                    return server.NOT_DONE_YET
                self._update_session_secret(session_id)
                reply_with_next_secret = True

        try:
            function = self._get_jsonrpc_method(function_name)
        except AttributeError as err:
            log.warning("Unknown method: %s", function_name)
            self._render_error(err, request, id_, version)
            return server.NOT_DONE_YET

        if args == EMPTY_PARAMS:
            d = defer.maybeDeferred(function)
        else:
            d = defer.maybeDeferred(function, *args)

        # cancel the response if the connection is broken
        notify_finish.addErrback(self._response_failed, d)
        d.addCallback(self._callback_render, request, id_, version, reply_with_next_secret)
        d.addErrback(
            log.fail(self._render_error, request, id_, version=version),
            'Failed to process %s', function_name
        )
        return server.NOT_DONE_YET

    def _register_user_session(self, session_id):
        """
        Add or update a HMAC secret for a session

        @param session_id:
        @return: secret
        """
        log.info("Register api session")
        token = APIKey.new(seed=session_id)
        self.sessions.update({session_id: token})

    def _unregister_user_session(self, session_id):
        log.info("Unregister API session")
        del self.sessions[session_id]

    def _response_failed(self, err, call):
        log.debug(err.getTraceback())

    def _set_headers(self, request, data, update_secret=False):
        if conf.settings.allowed_origin:
            request.setHeader("Access-Control-Allow-Origin", conf.settings.allowed_origin)
        request.setHeader("Content-Type", "text/json")
        request.setHeader("Content-Length", str(len(data)))
        if update_secret:
            session_id = request.getSession().uid
            request.setHeader(LBRY_SECRET, self.sessions.get(session_id).secret)

    def _render_message(self, request, message):
        request.write(message)
        request.finish()

    def _check_headers(self, request):
        return (
            self._check_header_source(request, 'Origin') and
            self._check_header_source(request, 'Referer'))

    def _check_header_source(self, request, header):
        """Check if the source of the request is allowed based on the header value."""
        source = request.getHeader(header)
        if not self._check_source_of_request(source):
            log.warning("Attempted api call from invalid %s: %s", header, source)
            return False
        return True

    def _check_source_of_request(self, source):
        if source is None:
            return True
        if conf.settings.API_INTERFACE == '0.0.0.0':
            return True
        server, port = self.get_server_port(source)
        return self._check_server_port(server, port)

    def _check_server_port(self, server, port):
        api = (conf.settings.API_INTERFACE, conf.settings.api_port)
        return (server, port) == api or self._is_from_allowed_origin(server, port)

    def _is_from_allowed_origin(self, server, port):
        if not conf.settings.allowed_origin:
            return False
        if conf.settings.allowed_origin == '*':
            return True
        allowed_server, allowed_port = self.get_server_port(conf.settings.allowed_origin)
        return (allowed_server, allowed_port) == (server, port)

    def get_server_port(self, origin):
        parsed = urlparse.urlparse(origin)
        server_port = parsed.netloc.split(':')
        assert len(server_port) <= 2
        if len(server_port) == 2:
            return server_port[0], int(server_port[1])
        else:
            return server_port[0], 80

    def _check_function_path(self, function_path):
        if function_path not in self.callable_methods:
            log.warning("Unknown method: %s", function_path)
            return False
        if not self.announced_startup:
            if function_path not in self.allowed_during_startup:
                log.warning("Cannot call %s during startup", function_path)
                return False
        return True

    def _get_jsonrpc_method(self, function_path):
        if not self._check_function_path(function_path):
            raise AttributeError(function_path)
        return self.callable_methods.get(function_path)

    def _initialize_session(self, session_id):
        if not self.sessions.get(session_id, False):
            self._register_user_session(session_id)
            return True
        return False

    def _verify_token(self, session_id, message, token):
        assert token is not None, InvalidAuthenticationToken
        to_auth = get_auth_message(message)
        api_key = self.sessions.get(session_id)
        assert api_key.compare_hmac(to_auth, token), InvalidAuthenticationToken

    def _update_session_secret(self, session_id):
        self.sessions.update({session_id: APIKey.new(name=session_id)})

    def _get_jsonrpc_version(self, version=None, id=None):
        if version:
            version_for_return = int(float(version))
        elif id and not version:
            version_for_return = jsonrpclib.VERSION_1
        else:
            version_for_return = jsonrpclib.VERSION_PRE1
        return version_for_return

    def _callback_render(self, result, request, id_, version, auth_required=False):
        result_for_return = result

        if version == jsonrpclib.VERSION_PRE1:
            if not isinstance(result, jsonrpclib.Fault):
                result_for_return = (result_for_return,)

        try:
            encoded_message = jsonrpclib.dumps(
                result_for_return, id=id_, version=version, default=default_decimal)
            self._set_headers(request, encoded_message, auth_required)
            self._render_message(request, encoded_message)
        except Exception as err:
            log.exception("Failed to render API response: %s", result)
            self._render_error(err, request, id_, version)

    def _render_response(self, result):
        return defer.succeed(result)
