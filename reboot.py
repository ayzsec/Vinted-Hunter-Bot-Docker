import os
password = os.getenv("PASS")
os.system("cd /home/vinted/vintedpy")
os.system("git pull")
os.popen("sudo -S %s"%("pkill -9 python"), 'w').write(password)
os.popen("sudo -S %s"%("reboot"), 'w').write(password)