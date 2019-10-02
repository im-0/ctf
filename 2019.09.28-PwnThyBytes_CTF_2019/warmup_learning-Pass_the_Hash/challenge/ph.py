from hashlib import *
import hashlib
import os 

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

def xor(s1,s2):
	return ''.join([chr(ord(s1[i]) ^ ord(s2[i % len(s2)])) for i in range(len(s1))])

def gen_salt(password):
	n = 64 - 2 * len(password)
	return os.urandom(n)

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

def verify_pass(salt,password,received_hash):
	if (combo_hash(salt,password,h_list,no_rounds) == received_hash):
		print "Congrats. Here's a flag for you:"
		g = open('flag.txt','r')
		print g.read()
		g.close()
	else:
		print 'EPIC FAIL'



password = os.urandom(20)

no_rounds = 16
h_list = [sha, sha1, ripemd160, sha256]

print 'Greetings! Give me some salts and I will give you some hashes'
exit_query = True
remaining = 1024
while(exit_query and remaining > 0):
	try:
		salt = raw_input().strip().decode('hex')
	except:
		exit()
	if len(password + salt + password) == 64:
		print combo_hash(salt, password, h_list, no_rounds).encode('hex')
	else:
		exit_query = False
	remaining -= 1

print "Here is the challenge salt:"
challenge_salt = gen_salt(password)
print challenge_salt.encode('hex')

challenge_hash = raw_input("\nGive me the challenge_hash ").strip().decode('hex')
verify_pass(challenge_salt,password,challenge_hash)
