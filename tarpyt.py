#!/usr/bin/env python

import BaseHTTPServer
import random
from zlib import adler32
from optparse import OptionParser
import pickle
import time

from genmarkov import MarkovBuilder, TagState, MarkovChain

class TarpytHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    pass

class Tarpyt(object):
    def __init__(self, builder=None):
        self.handler_class = TarpytHandler
        for verb in ('GET','POST','HEAD'):
            setattr(self.handler_class, 'do_'+verb, lambda h: self.pick_response(h)(h))
        self.handler_class.server_version = 'Apache/1.3.14'
        self.builder = builder
        if self.builder:
            def getlink(path='/'):
                pathlist = ['^']
                pathlist.extend(path.split('/'))
                elem = self.builder.uripaths.get(pathlist[-1])
                if elem == '$':
                    elem = chr(random.randint(0x61,0x7A))
                return '/'.join(pathlist[1:]+[elem])
            self.getlink = getlink
        else:
            def getlink(path='/'):
                next_path = path.rstrip('/') + '/{0}'
                return next_path.format(chr(random.randint(0x61,0x7A)))
            self.getlink = getlink
        self.responses = []
        self.responses.extend( (self.response_linkpage,) * 4 )
        self.responses.extend( (self.response_redirect,) * 1 )
        self.responses.extend( (self.response_inf_redirect,) * 1 )
        self.responses.extend( (self.response_oversize,) * 1 )
        self.responses.extend( (self.response_slow,) *1 )

    def response_slow(self, handler):
        """ Category: tarpit
        Returns an html page, but very slowly
        """
        content = None
        if self.builder:
            content = self.builder.generate()
        else:
            content = "A" * 4096
        handler.send_response(200)
        handler.send_header('Content-Length',len(content))
        handler.end_headers()
        for char in content:
            time.sleep(1)
            handler.wfile.write(char)

    def response_linkpage(self, handler):
        """ Category: tarpit
        Returns an html page full of links
        """
        page_string = "<html><head><title>Welcome to the Labyrinth</title></head><body><ul>{0}</ul></body></html>"
        link_string = '<li><a href="{0}">{0}</a></li>'
        links = []
        for n in range(0,5):
            href = self.getlink(handler.path)
            links.append(link_string.format(href))
        response_body = page_string.format(''.join(links))
        handler.send_response(200)
        handler.send_header('Content-Length',len(response_body))
        handler.end_headers()
        handler.wfile.write(response_body)

    def response_redirect(self, handler):
        """ Category: realism
        Redirects to a random page
        """
        handler.send_response(302)
        handler.send_header('Location',self.getlink())
        handler.end_headers()

    def response_inf_redirect(self, handler):
        """ Category: tarpit
        Returns a 302 redirect to a page which has the same modulus as the
        one requested, resulting in an infinite redirect. Loops eventually.
        If a suitable redirect cannot be made, falls back to appending a
        random path element to the path requested.
        """
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
        else:
            newpath = self.getlink(newpath)
        handler.send_response(302)
        handler.send_header('Location',newpath)
        handler.end_headers()

    def response_oversize(self, handler):
        """ Category: attack
        Sends an oversized Content-Length header. Some web servers have had
        Denial of Service vulnerabilities due to preallocating memory or disk
        (e.g. https://secunia.com/advisories/35645). Some spiders may have
        similar vulns (See, e.g., feature request for wget: 
        https://lists.gnu.org/archive/html/bug-wget/2012-01/msg00054.html)
        """
        handler.send_response(200)
        handler.send_header('Content-Length',4 * 2**30) #4GB
        handler.end_headers()

    def response_robots(self, handler):
        """ Category: safety
        Sends a robots.txt which disallows all paths for all robots. This
        should guarantee no innocent spiders get caught in our tarpit.
        """
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
