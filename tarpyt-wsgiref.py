#!/usr/bin/env python

from wsgiref.simple_server import make_server
from optparse import OptionParser
from tarpyt import Tarpyt

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-f', '--config',
            help='Tarpyt config file', metavar='FILE')
    (options, args) = parser.parse_args()
    tarpyt = Tarpyt(options.config)
    httpd = make_server('', 8080, tarpyt.application)
    httpd.serve_forever()
