TarPyt
======
TarPyt is a Python Web tarpit, inspired by a description of a PHP
equivalent called Labyrinth. It's an automated scanner's worst
nightmare, a maze of twisty URIs, all alike.

Features
--------
A random list of features, to be better organized later:

* "Random" different responses (HTTP redirects, link pages, etc.)
* Base response on a hash of the request, so it's consistent
* Generate Markov chains of HTML and URI paths for realistic responses

Todo
----
* Hide fingerprint (server header) or fake a real one
* Shell script to get top 100 Alexa sites and build markov chains
* Use Markov chains to build HTML in responses
* Infinite redirects
* False positives for scanners: SQLi (database errors), etc.
* abstract-out the functionality to use with WSGI, FastCGI, etc.

Attacks
-------
Possible ideas for cruelty to scanners/spiders:

* Pathological-case compression (high resource use for recipient)
* Artificially slow responses
* Huge content-length headers for agents that pre-allocate storage
  (may need to keep connection open, which is a negative)
* Broken markup: research edge cases for XML parsers
