import hashlib
import os 
import socket


def sha(my_string):
	m = hashlib.new('sha')
	m.update(my_string)
	return m.digest()

def sha1(my_string):
	m = hashlib.new('sha1')
	m.update(my_string)
	return m.digest()

def sha256(my_string):
	m = hashlib.new('sha256')
	m.update(my_string)
	return m.digest()

def ripemd160(my_string):
	m = hashlib.new('ripemd160')
	m.update(my_string)
	return m.digest()

no_rounds = 16
h_list = [sha, sha1, ripemd160, sha256]

def xor(s1,s2):
	return ''.join([chr(ord(s1[i]) ^ ord(s2[i % len(s2)])) for i in range(len(s1))])

def gen_salt():
	return os.urandom(24)

def combo_hash(salt,password,h_list,no_rounds):
	salted_pass = password + salt + password
	l_pass = salted_pass[:32]
	r_pass = salted_pass[32:]
	for i in range(no_rounds):
		l_index = ord(l_pass[31]) % len(h_list)
		r_index = ord(r_pass[0]) % len(h_list)
		l_hash = h_list[l_index](l_pass)
		r_hash = h_list[r_index](r_pass)
		l_pass = xor(l_pass,r_hash)
		r_pass = xor(r_pass,l_hash)
	return l_pass + r_pass


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('52.142.217.130', 13374))
sock = sock.makefile('rw')

print '< ', sock.readline().strip()

lvars, rvars = {}, {}
lvar, rvar = None, None
for _ in range(1024):
	test_salt = gen_salt()
	ls = test_salt[:12]
	rs = test_salt[12:]
	
	tx = test_salt.encode('hex')
	print '> ', tx
	sock.write(tx + '\n')
	sock.flush()
	rx = sock.readline().strip()
	print '< ', rx
	test_hash = rx.decode('hex')
	
	lh = test_hash[:32]
	rh = test_hash[32:]
	
	lhsp = lh[20:]
	rhsp = rh[:12]
	
	lshit = xor(lhsp, ls)
	rshit = xor(rhsp, rs)
	
	lpp = xor(lshit, lh)
	rpp = xor(rshit, rh[20:])

	if lpp in lvars:
		lvars[lpp] += 1
		if lvars[lpp] == 2:
			lvar = lpp
	else:
		lvars[lpp] = 1
	if rpp in rvars:
		rvars[rpp] += 1
		if rvars[rpp] == 2:
			rvar = rpp
	else:
		rvars[rpp] = 1
		
	if lvar and rvar:
		break

if not lvar or not rvar:
	raise RuntimeError('fuck')

pwd = lvar + rvar[-8:]

tx = ''
print '> ', tx
sock.write(tx + '\n')
sock.flush()

print '< ', sock.readline().strip()

rx = sock.readline().strip()
print '< ', rx
ch_salt = rx.decode('hex')

tx = combo_hash(ch_salt, pwd, h_list, no_rounds).encode('hex')
print '> ', tx
sock.write(tx + '\n')
sock.flush()

ne = 0
while ne < 5:
	rx = sock.readline().strip()
	if not rx:
		ne += 1
	print '< ', rx
