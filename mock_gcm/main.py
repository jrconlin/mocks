
import cyclone.web
import configargparse
from twisted.internet import reactor
from twisted.logger import Logger

from mock_gcm.gcm_handler import GCMHandler
from mock_gcm.log import LogObserver

log = Logger()

config_files = [
    "mock_gcm.ini"
]


def get_args(sysargs):
    parser = configargparse.ArgumentParser(
        description='Fakey GCM server',
        default_config_files=config_files,
    )
    parser.add_argument("--port", "-p", help="Port", type=int, default=0,
                        env_var="PORT")
    parser.add_argument("--log_level", "-l", help="Logging Level", type=str,
                        default="info", env_var="LOG_LEVEL")
    parser.add_argument("--debug", "-d", help="Enable debugging",
                        action="store_true", default=False, env_var="DEBUG")
    return parser.parse_args(sysargs)


def main(sysargs=None):
    args = get_args(sysargs)
    # log_level = args.log_level or ("debug" if args.debug else args.log_level)
    site = cyclone.web.Application([('/gcm/send', GCMHandler),
                                    ('/fcm/send', GCMHandler)])
    LogObserver().start()
    if not args.port:
        args.port = 8100
    reactor.listenTCP(args.port, site)
    reactor.run()
