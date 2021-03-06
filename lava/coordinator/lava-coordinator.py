#! /usr/bin/python3

#  Copyright 2013 Linaro Limited
#  Author Neil Williams <neil.williams@linaro.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import logging
import json
import os
import sys
import optparse
import daemon

try:
    import daemon.pidlockfile as pidlockfile
except ImportError:
    from lockfile import pidlockfile
from logging.handlers import WatchedFileHandler
from lava.coordinator import LavaCoordinator


def getDaemonLogger(filePath, log_format=None, loglevel=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    try:
        watchedHandler = WatchedFileHandler(filePath)
    except Exception as e:
        return e

    watchedHandler.setFormatter(logging.Formatter(log_format or "%(asctime)s %(msg)s"))
    logger.addHandler(watchedHandler)
    return logger, watchedHandler


def readSettings(filename):
    """
    NodeDispatchers need to use the same port and blocksize as the Coordinator,
    so read the same conffile.
    """
    settings = {
        "port": 3079,
        "coordinator_hostname": "localhost",
        "blocksize": 4 * 1024,
    }
    with open(filename) as stream:
        jobdata = stream.read()
        json_default = json.loads(jobdata)
    if "port" in json_default:
        settings["port"] = json_default["port"]
    if "blocksize" in json_default:
        settings["blocksize"] = json_default["blocksize"]
    if "coordinator_hostname" in json_default:
        settings["coordinator_hostname"] = json_default["coordinator_hostname"]
    return settings


if __name__ == "__main__":
    # instance settings come from django - the coordinator doesn't use django and is
    # not necessarily per-instance, so use the command line and a default conf file.
    pidfile = "/var/run/lava-coordinator.pid"
    logfile = "/var/log/lava-coordinator.log"
    conffile = "/etc/lava-coordinator/lava-coordinator.conf"
    settings = readSettings(conffile)
    usage = "Usage: %prog [--logfile] --[loglevel]"
    description = (
        "LAVA Coordinator singleton for LAVA (MultiNode support). The singleton "
        "can support multiple instances. If more than one "
        "Coordinator exists on one machine, each must use a unique port "
        "and should probably use a unique log-file. The directory specified for "
        "the logfile must exist or the default will be used instead."
        "Port number and blocksize are handled in %s" % conffile
    )
    parser = optparse.OptionParser(usage=usage, description=description)
    parser.add_option(
        "--logfile",
        dest="logfile",
        action="store",
        type="string",
        help="log file for the LAVA Coordinator daemon [%s]" % logfile,
    )
    parser.add_option(
        "--loglevel",
        dest="loglevel",
        action="store",
        type="string",
        help="logging level [INFO]",
    )
    (options, args) = parser.parse_args()
    if options.logfile:
        if os.path.exists(os.path.dirname(options.logfile)):
            logfile = options.logfile
        else:
            print("No such directory for specified logfile '%s'" % logfile)
    open(logfile, "w").close()
    level = logging.INFO
    if options.loglevel == "DEBUG":
        level = logging.DEBUG
    if options.loglevel == "WARNING":
        level = logging.WARNING
    if options.loglevel == "ERROR":
        level = logging.ERROR
    client_logger, watched_file_handler = getDaemonLogger(logfile, loglevel=level)
    if isinstance(client_logger, Exception):
        print("Fatal error creating client_logger: " + str(client_logger))
        sys.exit(os.EX_OSERR)
    # noinspection PyArgumentList
    lockfile = pidlockfile.PIDLockFile(pidfile)
    if lockfile.is_locked():
        logging.error("PIDFile %s already locked" % pidfile)
        sys.exit(os.EX_OSERR)
    context = daemon.DaemonContext(
        detach_process=True,
        working_directory=os.getcwd(),
        pidfile=lockfile,
        files_preserve=[watched_file_handler.stream],
        stderr=watched_file_handler.stream,
        stdout=watched_file_handler.stream,
    )
    starter = {
        "coordinator": True,
        "logging_level": options.loglevel,
        "host": settings["coordinator_hostname"],
        "port": settings["port"],
        "blocksize": settings["blocksize"],
    }
    with context:
        logging.info(
            "Running LAVA Coordinator %s %s %d."
            % (logfile, settings["coordinator_hostname"], settings["port"])
        )
        LavaCoordinator(starter).run()
