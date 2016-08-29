# hashcache

``hashcache`` processes directories recursively and calculates the MD5 and 
SHA-256 digests for each file encountered. The result is cached and stored in an 
SQLite database and will only be recalculated if the file has changed.

Files are identified using their inode number (``st_ino``) and device ID 
(``st_dev``) which means that they can be renamed and moved around. Only moving 
the files to another filesystem will require the digests to be recalculated.

## Examples

Calculate digests for the first time:

	$ hashcache.py /home/jukka/git/hashcache/
	2016-08-29 16:33:13,766 [INFO] - Hashing: /home/jukka/git/hashcache/hashcache.py
	2016-08-29 16:33:13,768 [INFO] - Hashing: /home/jukka/git/hashcache/LICENSE
	2016-08-29 16:33:13,771 [INFO] - Hashing: /home/jukka/git/hashcache/README.md

Change a file and recalculate the digest for that file:

	$ touch /home/jukka/git/hashcache/hashcache.py
	$ hashcache.py /home/jukka/git/hashcache/
	2016-08-29 16:33:44,163 [INFO] - Hashing: /home/jukka/git/hashcache/hashcache.py

Output SHA-256 digests from the cache:

	$ hashcache.py --print-sha256 /home/jukka/git/hashcache/
	ce7db4afb09c2c9549542e1b43fb0e14825ac6981f76dbff11e5621fc77ab420  /home/jukka/git/hashcache/hashcache.py
	a772af9aeb1f52c4c65d5ca647e6886ad19b29b115544e3bd2c63cea43fa88e3  /home/jukka/git/hashcache/LICENSE
	150cc6b4f57203a1465f0007c47a4edcaf7ceca807f64b8d30977f519b91ccf6  /home/jukka/git/hashcache/README.md

## Requirements

On Linux systems, Python >=3.3 is required because the tool uses ``st_mtime_ns`` 
for tracking modification time with nanosecond resolution.

On Windows the minimum supported version is Python 3.4 because in earlier 
versions ``st_dev`` and ``st_ino`` were filled with dummy values.
