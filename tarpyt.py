#!/usr/bin/env python

from wsgiref.simple_server import make_server
import random
from zlib import adler32
from optparse import OptionParser
import pickle
import time
#import sys #stderr

from genmarkov import MarkovBuilder, TagState, MarkovChain

class Tarpyt(object):
    def __init__(self, builder=None):
        self.builder = builder
        if self.builder:
            def getlink(path='/'):
                pathlist = ['^']
                pathlist.extend(filter(lambda x: x, path.split('/')))
                elem = self.builder.uripaths.get(pathlist[-1])
                if elem == '$':
                    elem = self.builder.uripaths.get(None)
                return '/'+'/'.join(pathlist[1:]+[elem])
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

    def response_slow(self, environ, start_response):
        """ Category: tarpit
        Returns an html page, but very slowly
        """
        content = None
        if self.builder:
            content = self.builder.generate(generate_links=True)
        else:
            content = u"A" * 4096
        status = '200 OK'
        headers = [('Content-Length',str(len(content)))]
        start_response(status, headers)
        for char in content.encode('utf-8'):
            yield char
            time.sleep(1)

    def response_linkpage(self, environ, start_response):
        """ Category: tarpit
        Returns an html page full of links
        """
        response_body = None
        if self.builder:
            response_body = self.builder.generate(generate_links=True)
        else:
            page_string = "<html><head><title>Welcome to the Labyrinth</title></head><body><ul>{0}</ul></body></html>"
            link_string = '<li><a href="{0}">{0}</a></li>'
            links = []
            prev_href = ''
            for n in range(0,5):
                href = self.getlink(environ['PATH_INFO'])
                if href == prev_href:
                    href = self.getlink('/'+chr(random.randint(0x61,0x7A)))
                else:
                    prev_href = href
                links.append(link_string.format(href))
            response_body = page_string.format(''.join(links))
        status = '200 OK'
        start_response(status, [])
        if isinstance(response_body, unicode):
            response_body = response_body.encode('utf-8')
        return [response_body]

    def response_redirect(self, environ, start_response):
        """ Category: realism
        Redirects to a random page
        """
        status = '302 Found'
        location = self.getlink()
        if isinstance(location, unicode):
            location = urllib.quote(location.encode('utf-8'))
        headers = [('Location', location)]
        start_response(status, headers)
        return ""

    def response_inf_redirect(self, environ, start_response):
        """ Category: tarpit
        Returns a 302 redirect to a page which has the same modulus as the
        one requested, resulting in an infinite redirect. Loops eventually.
        If a suitable redirect cannot be made, falls back to appending a
        random path element to the path requested.
        """
        path = environ['PATH_INFO']
        modulus = len(self.responses)
        newpath = path
        tmp = 0
        chord = 0
        pos = len(path) - 1
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
        status = '302 Found'
        if isinstance(newpath, unicode):
            newpath = urllib.quote(newpath.encode('utf-8'))
        headers = [('Location', newpath)]
        start_response(status, headers)
        return ""

    def response_oversize(self, environ, start_response):
        """ Category: attack
        Sends an oversized Content-Length header. Some web servers have had
        Denial of Service vulnerabilities due to preallocating memory or disk
        (e.g. https://secunia.com/advisories/35645). Some spiders may have
        similar vulns (See, e.g., feature request for wget: 
        https://lists.gnu.org/archive/html/bug-wget/2012-01/msg00054.html)
        """
        status = '200 OK'
        headers = [('Content-Length', str(4 * 2**30))]
        start_response(status, headers)
        return ["",""] #Prevent WSGI from calculating content-length

    def response_robots(self, environ, start_response):
        """ Category: safety
        Sends a robots.txt which disallows all paths for all robots. This
        should guarantee no innocent spiders get caught in our tarpit.
        """
        robots = "User-agent: *\nDisallow: /\n"
        status = '200 OK'
        start_response(status, [])
        return [robots]

    def application(self, environ, start_response):
        verb = environ['REQUEST_METHOD']
        path = environ['PATH_INFO']
        if path == '/robots.txt' and verb == 'GET':
            #play nice with robots
            return self.response_robots(environ, start_response)
        index = adler32(verb + path) % len(self.responses)
        return self.responses[index](environ, start_response)

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-m', '--markov',
            help='A pickled MarkovBuilder', metavar='FILE')
    (options, args) = parser.parse_args()
    builder = None
    if options.markov:
        mfile = open(options.markov, 'rb')
        builder = pickle.load(mfile)
        mfile.close()
    tarpyt = Tarpyt(builder=builder)
    httpd = make_server('', 8080, tarpyt.application)
    httpd.serve_forever()
