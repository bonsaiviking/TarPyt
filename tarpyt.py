#!/usr/bin/env python

import BaseHTTPServer
import random

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
    server_version = 'Apache/1.3.14'
    page_string = "<html><head><title>Welcome to the Labyrinth</title></head><body><ul>{0}</ul></body></html>"
    link_string = '<li><a href="{0}">{0}</a></li>'
    def do_GET(self):
        links = []
        next_path = self.path.rstrip('/') + '/{0}'
        for n in range(0,5):
            href = next_path.format(chr(random.randint(0x61,0x7A)))
            links.append(RequestHandler.link_string.format(href))
        response_body = RequestHandler.page_string.format(''.join(links))
        self.send_response(200)
        self.send_header('Content-Length',len(response_body))
        self.end_headers()
        self.wfile.write(response_body)

def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
    httpd = server_class(('',8080), handler_class)
    httpd.serve_forever()

if __name__=='__main__':
    run(handler_class=RequestHandler)
