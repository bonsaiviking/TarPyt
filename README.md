TarPyt
======
TarPyt is a Python Web tarpit, inspired by a description of a PHP
equivalent called [Labyrinth](https://code.google.com/p/weblabyrinth/).
It's an automated scanner's worst nightmare, a maze of twisty URIs, all alike.

Running TarPyt
--------------

TarPyt can be run on its own, or as a
[WSGI](http://wsgi.readthedocs.org/en/latest/index.html) app. In its current
(testing) state, running under a separate webserver as a WSGI app has not been
tested, but should work just fine. To run standalone, just run:

    python tarpyt.py

Generating Markov chains
------------------------

The included `genmarkov.py` can be used to generate and
[pickle](http://docs.python.org/library/pickle.html) a simple Markov chain for
building html-like content. I've had decent luck pointing it at the
[Alexa](http://www.alexa.com/topsites) top 20 web sites, downloaded with
`wget`. Currently, TarPyt only uses these chains to generate urls, but full
pages will be coming soon.

Features
--------
A random list of features, to be better organized later:

* WSGI-compatible interface
* "Random" different responses (HTTP redirects, link pages, etc.)
* Base response on a hash of the request, so it's consistent
* Generate Markov chains of HTML and URI paths for realistic responses
* Infinite redirects, slow responses
* Artificially slow responses (1 Bps)
* Artificially large (4GB) content-length headers for agents that pre-allocate storage

Todo
----
* Shell script to get top 100 Alexa sites and build markov chains
* Use Markov chains to build HTML in responses
* False positives for scanners: SQLi (database errors), etc.
* Alerting, stats?

Attacks
-------
Possible ideas for cruelty to scanners/spiders:

* Pathological-case compression (high resource use for recipient)
* Broken markup: research edge cases for XML parsers
