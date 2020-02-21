import subprocess
import os

serial = subprocess.check_output(['cat', '/proc/cpuinfo'])[-5:-1].decode('utf-8')
hostname = "SUN_NODE" + "_" + serial
host_string = "127.0.1.1	"
os.system("echo " + hostname + " > /usr/lib/sun/hostname")
os.system("rm /etc/hosts")
os.system("cp /usr/lib/sun/static_files/hosts /etc/")
os.system("echo " + host_string + hostname + " >> /etc/hosts")
