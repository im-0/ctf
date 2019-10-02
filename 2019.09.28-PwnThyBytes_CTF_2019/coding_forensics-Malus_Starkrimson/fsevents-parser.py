#!/bin/env python3
#
# http://nicoleibrahim.com/apple-fsevents-forensics/

import sys
import struct


def readb(fl, sz):
	buf = fl.read(sz)
	if not buf:
		# EOF
		exit(0)
	if len(buf) != sz:
		raise RuntimeError('Fmt err: %r != %r', (len(buf), sz))
	return buf


def swap32(i):
	return struct.unpack("<I", struct.pack(">I", i))[0]


def dec_reason(fl):
	fl = swap32(fl)
	for fv, ft in {
			0x00000001: 'Item is Folder',
			0x00000002: 'Mount',
			0x00000004: 'Unmount',
			0x00000020: 'End of Transaction',
			0x00000800: 'Last Hard Link Removed',
			0x00001000: 'Item is Hard Link',
			0x00004000: 'Item is Symbolic Link',
			0x00008000: 'Item is File',
			0x00010000: 'Permissions Changed',
			0x00020000: 'Extended Attributes Modified',
			0x00040000: 'Extended Attributes Removed',
			0x00100000: 'Document Revisions Changed',
			0x00400000: 'Item Cloned',
			0x01000000: 'Created',
			0x02000000: 'Removed',
			0x04000000: 'Inode Metadata Modified',
			0x08000000: 'Renamed',
			0x10000000: 'Content Modified',
			0x20000000: 'Exchange',
			0x40000000: 'Finder Information Modified',
			0x80000000: 'Folder Created'}.items():
		if fl & fv:
			print('        ', ft)


f = open(sys.argv[1], 'rb')


magic = readb(f, 4)
if magic == b'1SLD':
	ver = 1
elif magic == b'2SLD':
	ver = 2
else:
	raise RuntimeError('Bad magic: %r' % (magic, ))

print('VERSION: ', ver)

# Unknown value.
_ = readb(f, 4)

size = readb(f, 4)
size = struct.unpack('<I', size)[0]
print('SIZE: ', size)

while True:
	fname = b''
	b = True
	while b:
		b = readb(f, 1);
		if b == b'\x00':
			break
		fname += b
	fname = fname.decode('utf-8')
	print('fname: ', fname)
	
	if ver == 1:
		buf = readb(f, 12) + b'\x00' * 8
	else:
		buf = readb(f, 20)

	ev_id, reason_fl, node_id = struct.unpack('<QIQ', buf)
	if reason_fl != 8388625 or True:
		print('    event id: ', ev_id)
		print('    reason: ', reason_fl)
		dec_reason(reason_fl)
		print('    node id: ', node_id)
