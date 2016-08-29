#!/usr/bin/env python3

import argparse
import binascii
import hashlib
import logging
import os
import sqlite3
import sys
import traceback

def get_digests(filename):
	md5 = hashlib.md5()
	sha256 = hashlib.sha256()
	with open(filename, 'rb') as file:
		for block in iter(lambda: file.read(262144), b''):
			md5.update(block)
			sha256.update(block)
	return md5.digest(), sha256.digest()

def walk(top):
	for dirpath, dirnames, filenames in os.walk(top):
		for filename in filenames:
			filepath = os.path.join(dirpath, filename)
			yield filepath

def migrate_database(cursor):
	cursor.execute('PRAGMA user_version')
	user_version = cursor.fetchone()[0]

	if user_version < 1:
		cursor.execute('CREATE TABLE digest (dev INTEGER, ino INTEGER, size INTEGER, time INTEGER, md5 BLOB, sha256 BLOB, PRIMARY KEY (dev, ino))')
		cursor.execute('PRAGMA user_version = 1')

def main(argv=None):
	if argv is None:
		argv = sys.argv[1:]

	logging.basicConfig(
		level=logging.INFO,
		format='%(asctime)s [%(levelname)s] - %(message)s'
	)

	dbpath = os.path.join(
		os.getenv('HOME') or os.getenv('USERPROFILE'),
		'.hashcache'
	)

	parser = argparse.ArgumentParser()
	parser.add_argument('--print-md5', action='store_const', dest='print', const='md5')
	parser.add_argument('--print-sha256', action='store_const', dest='print', const='sha256')
	parser.add_argument('--database', default=dbpath)
	parser.add_argument('files', metavar='FILE', nargs='+')
	args = parser.parse_args(argv)

	connection = sqlite3.connect(args.database)
	cursor = connection.cursor()
	cursor.execute('PRAGMA synchronous = 0')
	migrate_database(cursor)
	connection.commit()

	for arg in args.files:
		filenames = walk(arg) if os.path.isdir(arg) else [arg]

		for filename in filenames:
			original_filename = filename
			if sys.platform == 'win32':
				# http://stackoverflow.com/questions/1857335/is-there-any-length-limits-of-file-path-in-ntfs
				filename = '\\\\?\\' + os.path.abspath(filename)

			if os.path.islink(filename) or not os.path.isfile(filename):
				continue

			try:
				statinfo = os.stat(filename)
			except PermissionError:
				traceback.print_exc()
				continue

			cursor.execute(
				'SELECT md5, sha256 FROM digest WHERE dev = ? AND ino = ? AND size = ? AND time = ?',
				(statinfo.st_dev, statinfo.st_ino, statinfo.st_size, statinfo.st_mtime_ns)
			)
			row = cursor.fetchone()

			if row is None:
				logging.info('Hashing: %s', original_filename)
				try:
					md5, sha256 = get_digests(filename)
				except IOError:
					traceback.print_exc()
					continue
				cursor.execute(
					'INSERT OR REPLACE INTO digest VALUES (?, ?, ?, ?, ?, ?)',
					(statinfo.st_dev, statinfo.st_ino, statinfo.st_size, statinfo.st_mtime_ns, md5, sha256)
				)
				connection.commit()
			else:
				md5, sha256 = row[0], row[1]

			if args.print:
				if args.print == 'md5':
					digest = md5
				elif args.print == 'sha256':
					digest = sha256

				sys.stdout.buffer.write('{}  {}\n'.format(
					binascii.hexlify(digest).decode('ascii'),
					original_filename
				).encode('utf8'))

	cursor.close()
	connection.close()

	return 0

if __name__ == "__main__":
	sys.exit(main())
