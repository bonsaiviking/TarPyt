TarPyt
======
TarPyt is a Python Web tarpit, inspired by a description of a PHP
equivalent called Labyrinth. It's an automated scanner's worst
nightmare, a maze of twisty URIs, all alike.

Todo
----
* Hide fingerprint (server header) or fake a real one
* Get a corpus of uris and build a Markov chain for paths
* Random different responses (HTTP codes, attacks, etc.)
* Base response on a hash of the request, so it's consistent?
* Infinite redirects
* False positives for scanners: SQLi (database errors), etc.

Attacks
-------
Possible ideas for cruelty to scanners/spiders:

* Pathological-case compression (high resource use for recipient)
* Artificially slow responses
* Huge content-length headers for agents that pre-allocate storage
  (may need to keep connection open, which is a negative)
* Broken markup: research edge cases for XML parsers
