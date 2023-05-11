import os

if os.name != "win32":
	try:
		open('sudo ifconfig eth0 192.168.1.1 netmask 255.255.255.0')
	except Exception as error:
		print(f'[ERROR] Error while changing local ip (in adds.py): {error}')