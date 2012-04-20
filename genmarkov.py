#!/usr/bin/env python

from HTMLParser import HTMLParser, HTMLParseError
from optparse import OptionParser
import fileinput
import pickle
import random
import sys
from codecs import open

class MarkovChain(object):
    def __init__(self):
        self.words = {}
        self.maxcount = 0

    def add(self, prev_word, next_word):
        if not (prev_word in self.words):
            self.words[prev_word] = {}
        if not (next_word in self.words[prev_word]):
            self.words[prev_word][next_word] = 0
        self.words[prev_word][next_word] += 1
        self.maxcount = max(self.maxcount, self.words[prev_word][next_word])

    def get(self, prev_word):
        if not (prev_word in self.words):
            return '$'
        followers = self.words[prev_word]
        allcounts = sum(followers.itervalues())
        randval = random.randint(1,allcounts)
        partial_sum = 0
        for word, count in followers.iteritems():
            partial_sum += count
            if partial_sum >= randval:
                return word

class TagState(object):
    def __init__(self, tag=None, prev='^'):
        self.prev_child = prev
        self.tag = tag

class MarkovBuilder(HTMLParser, object):
    def setup_chain(self):
        self.siblings = MarkovChain()
        self.children = MarkovChain()
        self.attrs = MarkovChain()
        self.data = MarkovChain()
        self.uripaths = MarkovChain()
        self.tagstack = [TagState()]
        self.maxsibs = 0
        self.maxdepth = 0
        self.gendepth = 0
        self.popped = True

    def handle_starttag(self, tag, attrs):
        self.popped = False
        state = self.tagstack[-1]
        #print >>sys.stderr, "{0: >10}{1}{2}".format(state.tag," "*len(self.tagstack), tag)
        if state.tag in ('meta','input','img','br','script','style','link'):
            self.handle_endtag(state.tag)
            state = self.tagstack[-1]
        if state.prev_child == '^':
            self.children.add(state.tag, tag)
        else:
            self.siblings.add(state.prev_child, tag)
        state.prev_child = tag
        prev_attr = tag
        for attr in attrs:
            if attr[0] == 'href':
                prev_path = '^'
                elems = attr[1].split('/')
                if len(elems) > 1 and elems[1] == '':
                    elems = elems[3:]
                for elem in elems:
                    self.uripaths.add(prev_path, elem)
                    prev_path = elem
                self.uripaths.add(prev_path, '$')
            str_attr = u'{0}="{1}"'.format(*attr)
            self.attrs.add(prev_attr, str_attr)
            prev_attr = str_attr
        self.attrs.add(prev_attr, '$')
        newstate = TagState(tag=tag)
        self.tagstack.append(newstate)
        self.maxdepth = max(self.maxdepth, len(self.tagstack))

    def handle_endtag(self, tag):
        state = self.tagstack.pop()
        if len(self.tagstack) == 0:
            self.tagstack = [TagState()]
        if state.prev_child == '^':
            self.children.add(state.tag, '$')
        if self.popped:
            self.siblings.add(state.tag, '$')
        self.popped = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        self.data.add(self.tagstack[-1].tag, data)

    def unknown_decl(self, data):
        pass

    def save(self, filename='html.mkv'):
        out = open(filename, mode='wb')
        pickle.dump(self, out, protocol=2)

    def generate(self, tag='html'):
        out = []
        while tag != '$': #Goes forever-ish?
        #for _ in xrange(self.siblings.maxcount):
        #    if tag == '$': break
            contents = []
            attr = tag
            while attr != '$':
                contents.append(attr)
                attr = self.attrs.get(attr)
            out.append(u'<{0}>\n'.format(' '.join(contents)).encode('utf-8'))
            data = self.data.get(tag)
            if data and data != '$':
                out.append(data.encode('utf-8'))
            first_child = self.children.get(tag)
            if first_child and first_child != '$':
                self.gendepth += 1
                if self.gendepth <= self.maxdepth:
                    out.append(self.generate(first_child))
            out.append(u'</{0}>\n'.format(tag).encode('utf-8'))
            tag = self.siblings.get(tag)
        return ''.join(out)

    def reset(self):
        super(MarkovBuilder, self).reset()
        self.tagstack = [TagState()]

class GotCharset(Exception):
    def __init__(self, charset):
        assert charset
        self.charset = charset

class EncodingDetector(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            attrhash = {}
            for attr in attrs:
                attrhash[attr[0]] = attr[1]
            if 'charset' in attrhash:
                raise GotCharset, attrhash['charset']
            elif 'http-equiv' in attrhash:
                if attrhash['http-equiv'].lower() == 'content-type':
                    for chunk in attrhash['content'].split(';'):
                        if 'charset' in chunk:
                            raise GotCharset, chunk.split('=')[-1]

def parse(filenames):
    builder = MarkovBuilder()
    builder.setup_chain()
    for fname in filenames:
        filein = open(fname, mode='rb', encoding='utf-8', errors='replace')
        try:
            try:
                getcharset = EncodingDetector()
                for line in filein:
                    getcharset.feed(line)
            except GotCharset as e:
                filein.close()
                filein = open(fname, mode='rb', encoding=e.charset, errors='replace')
            filein.seek(0)
            builder.feed(filein.read())
            builder.close()
        except HTMLParseError:
            pass
        builder.reset()
        filein.close()
    return builder


if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-p', '--pickle',
            help='Pickle the MarkovBuilder into FILE', metavar='FILE')
    (options, args) = parser.parse_args()
    builder = parse(args)
    if options.pickle:
        builder.save(options.pickle)
    print builder.generate()
