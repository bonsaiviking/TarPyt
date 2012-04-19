#!/usr/bin/env python

import BaseHTTPServer
import random
from zlib import adler32
from optparse import OptionParser
import pickle

from genmarkov import MarkovBuilder, TagState, MarkovChain

class TarpytHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    pass

class Tarpyt(object):
    def __init__(self, builder=None):
        self.handler_class = TarpytHandler
        for verb in ('GET','POST','HEAD'):
            setattr(self.handler_class, 'do_'+verb, lambda h: self.pick_response(h)(h))
        self.handler_class.server_version = 'Apache/1.3.14'
        self.page_string = "<html><head><title>Welcome to the Labyrinth</title></head><body><ul>{0}</ul></body></html>"
        self.link_string = '<li><a href="{0}">{0}</a></li>'
        self.builder = builder
        self.responses = []
        self.responses.extend( (self.response_linkpage,) * 3 )
        self.responses.extend( (self.response_redirect,) * 1 )
        self.responses.extend( (self.response_inf_redirect,) * 1 )

    def response_linkpage(self, handler):
        links = []
        getlink = None
        if self.builder:
            pathlist = ['^']
            pathlist.extend(handler.path.split('/')[:-1])
            getlink = lambda: '/'.join(pathlist[1:]+[self.builder.uripaths.get(pathlist[-1])]).rstrip('$')
        else:
            next_path = handler.path.rstrip('/') + '/{0}'
            getlink = lambda: next_path.format(chr(random.randint(0x61,0x7A)))
        for n in range(0,5):
            href = getlink()
            links.append(self.link_string.format(href))
        response_body = self.page_string.format(''.join(links))
        handler.send_response(200)
        handler.send_header('Content-Length',len(response_body))
        handler.end_headers()
        handler.wfile.write(response_body)

    def response_redirect(self, handler):
        handler.send_response(302)
        handler.send_header('Location','/'+chr(random.randint(0x61,0x7A)))
        handler.end_headers()

    def response_inf_redirect(self, handler):
        modulus = len(self.responses)
        newpath = handler.path
        tmp = 0
        chord = 0
        pos = len(handler.path) - 1
        while pos > 0:
            chord = ord(newpath[pos])
            tmp = chord + modulus
            while tmp != chord:
                if tmp > ord('z'):
                    tmp %= modulus
                if (tmp >= 0x30 and tmp <= 0x39) \
                        or (tmp >= 0x41 and tmp <= 0x5A) \
                        or (tmp >= 0x61 and tmp <= 0x7A):
                            break
                tmp += modulus
            if tmp == chord:
                pos -= 1
            else:
                break
        if pos != 0:
            newpath = newpath[:pos] + chr(tmp) + newpath[pos+1:]
        handler.send_response(302)
        handler.send_header('Location',newpath)
        handler.end_headers()

    def response_robots(self, handler):
        robots = "User-agent: *\nDisallow: /\n"
        handler.send_response(200)
        handler.send_header('Content-Length',len(robots))
        handler.end_headers()
        handler.wfile.write(robots)

    def pick_response(self, handler):
        if handler.path == '/robots.txt' and handler.command == 'GET':
            #play nice with robots
            return self.response_robots
        index = adler32(handler.command + handler.path) % len(self.responses)
        return self.responses[index]

    def run(self):
        server_class=BaseHTTPServer.HTTPServer
        httpd = server_class(('',8080), self.handler_class)
        httpd.serve_forever()

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-m', '--markov',
            help='A pickled MarkovBuilder', metavar='FILE')
    (options, args) = parser.parse_args()
    builder = None
    if options.markov:
        mfile = open(options.markov, 'rb')
        builder = pickle.load(mfile)
    Tarpyt(builder=builder).run()
