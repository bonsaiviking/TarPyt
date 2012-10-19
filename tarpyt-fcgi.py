#!/usr/bin/env python

from flup.server.fcgi import WSGIServer
from optparse import OptionParser
from tarpyt import Tarpyt

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-f', '--config',
            help='Tarpyt config file', metavar='FILE')
    (options, args) = parser.parse_args()
    tarpyt = Tarpyt(options.config)
    WSGIServer(tarpyt.application).run()
