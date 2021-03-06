from lbrynet.core import log_support

import argparse
import logging.handlers

from twisted.internet import defer, reactor
from jsonrpc.proxy import JSONRPCProxy

from lbrynet import analytics
from lbrynet import conf
from lbrynet.core import utils
from lbrynet.lbrynet_daemon.auth.client import LBRYAPIClient
from lbrynet.lbrynet_daemon.DaemonServer import DaemonServer


log = logging.getLogger(__name__)


def test_internet_connection():
    return utils.check_connection()


def stop():
    conf.initialize_settings()
    log_support.configure_console()
    try:
        LBRYAPIClient.get_client().call('stop')
    except Exception:
        log.exception('Failed to stop deamon')
    else:
        log.info("Shutting down lbrynet-daemon from command line")


def start():
    conf.initialize_settings()
    parser = argparse.ArgumentParser(description="Launch lbrynet-daemon")
    parser.add_argument("--wallet",
                        help="lbryum or ptc for testing, default lbryum",
                        type=str,
                        default=conf.LBRYUM_WALLET)
    parser.add_argument("--ui", help="path to custom UI folder", default=None)
    parser.add_argument(
        "--branch",
        help='Branch of lbry-web-ui repo to use, defaults to {}'.format(conf.settings.ui_branch),
        default=conf.settings.ui_branch)
    parser.add_argument('--no-launch', dest='launchui', action="store_false")
    parser.add_argument("--http-auth", dest="useauth", action="store_true")
    parser.add_argument(
        '--log-to-console', dest='logtoconsole', action='store_true',
        help=('Set to enable console logging. Set the --verbose flag '
              ' to enable more detailed console logging'))
    parser.add_argument(
        '--quiet', dest='quiet', action="store_true",
        help=('If log-to-console is not set, setting this disables all console output. '
              'If log-to-console is set, this argument is ignored'))
    parser.add_argument(
        '--verbose', nargs="*",
        help=('Enable debug output. Optionally specify loggers for which debug output '
              'should selectively be applied.'))
    args = parser.parse_args()

    conf.initialize_settings()
    utils.setup_certs_for_windows()

    conf.update_settings_from_file()
    update_settings_from_args(args)

    lbrynet_log = conf.settings.get_log_filename()
    log_support.configure_logging(lbrynet_log, args.logtoconsole, args.verbose)
    log.debug('Final Settings: %s', conf.settings.get_dict())

    try:
        log.debug('Checking for an existing lbrynet daemon instance')
        JSONRPCProxy.from_url(conf.settings.API_CONNECTION_STRING).is_running()
        log.info("lbrynet-daemon is already running")
        if not args.logtoconsole:
            print "lbrynet-daemon is already running"
        return
    except Exception:
        log.debug('No lbrynet instance found, continuing to start')
        pass

    log.info("Starting lbrynet-daemon from command line")

    if not args.logtoconsole and not args.quiet:
        print "Starting lbrynet-daemon from command line"
        print "To view activity, view the log file here: " + lbrynet_log
        print "Web UI is available at http://%s:%i" % (
            conf.settings.API_INTERFACE, conf.settings.api_port)
        print "JSONRPC API is available at " + conf.settings.API_CONNECTION_STRING
        print "To quit press ctrl-c or call 'stop' via the API"

    if test_internet_connection():
        analytics_manager = analytics.Manager.new_instance()
        start_server_and_listen(args.launchui, args.useauth, analytics_manager)
        reactor.run()

        if not args.logtoconsole and not args.quiet:
            print "\nClosing lbrynet-daemon"
    else:
        log.info("Not connected to internet, unable to start")
        if not args.logtoconsole:
            print "Not connected to internet, unable to start"
        return


def update_settings_from_args(args):
    to_pass = {}
    if args.ui:
        to_pass['local_ui_path'] = args.ui
    if args.branch:
        to_pass['ui_branch'] = args.branch
    to_pass['use_auth_http'] = args.useauth
    to_pass['wallet'] = args.wallet
    conf.settings.update(to_pass)


@defer.inlineCallbacks
def start_server_and_listen(launchui, use_auth, analytics_manager):
    """The primary entry point for launching the daemon.

    Args:
        launchui: set to true to open a browser window
        use_auth: set to true to enable http authentication
        analytics_manager: to send analytics
    """
    analytics_manager.send_server_startup()
    log_support.configure_analytics_handler(analytics_manager)
    try:
        daemon_server = DaemonServer(analytics_manager)
        yield daemon_server.start(use_auth, launchui)
        analytics_manager.send_server_startup_success()
    except Exception as e:
        log.exception('Failed to startup')
        analytics_manager.send_server_startup_error(str(e))
        reactor.callFromThread(reactor.stop)


if __name__ == "__main__":
    start()
