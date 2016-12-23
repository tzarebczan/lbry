#!/usr/bin/env python

import sys
import os
from pip import req as pip_req, download as pip_download
from lbrynet import __version__

LINUX = 'linux'
DARWIN = 'darwin'
WINDOWS = 'win32'

if sys.platform.startswith("linux"):
    platform = LINUX
elif sys.platform.startswith("darwin"):
    platform = DARWIN
elif sys.platform.startswith("win"):
    platform = WINDOWS
else:
    raise Exception("Unknown os: %s" % sys.platform)


def package_files(directory):
    for path, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.join('..', path, filename)


def get_requirements_and_links():
    links = []
    reqs = []
    requirement_sources = pip_req.parse_requirements('requirement_links.txt', session=pip_download.PipSession())
    requirements = pip_req.parse_requirements('requirements.txt', session=pip_download.PipSession())

    for item in requirement_sources:
        if getattr(item, 'link', None) and getattr(item, 'link', None):  # newer pip has link
            links.append(str(item.link))
            reqs.append(str(item.req))

    for item in requirements:
        if item.req:
            reqs.append(str(item.req))
        if getattr(item, 'markers', None):
            if item.markers is not None:
                # remove OS specific requirements
                if not item.markers.evaluate():
                    reqs.remove(str(item.req))

    return reqs, links


# TODO: fix miniupnpc on appveyor

base_dir = os.path.abspath(os.path.dirname(__file__))
package_name = "lbrynet"
dist_name = "LBRY"
description = "A decentralized media library and marketplace"
author = "LBRY, Inc"
url = "lbry.io"
maintainer = "Jack Robison"
maintainer_email = "jack@lbry.io"
keywords = "LBRY"
console_scripts = [
    'lbrynet-daemon = lbrynet.lbrynet_daemon.DaemonControl:start',
    'stop-lbrynet-daemon = lbrynet.lbrynet_daemon.DaemonControl:stop',
    'lbrynet-cli = lbrynet.lbrynet_daemon.DaemonCLI:main'
]
package_data = {package_name: list(package_files('lbrynet/resources/ui'))}
entry_points = {'console_scripts': console_scripts}
requires, dependency_links = get_requirements_and_links()

if platform in [LINUX, DARWIN]:
    from setup_unix import setup
else:
    from setup_win32 import setup

setup(requires, package_name, platform, description, __version__, maintainer, maintainer_email, url, author,
      keywords, base_dir, entry_points, package_data, dependency_links, [])