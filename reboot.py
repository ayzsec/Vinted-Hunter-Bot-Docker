import os
password = os.getenv("PASS")
os.system("cd /home/vinted/vintedpy")
os.system("git pull")
os.popen("sudo pkill -9 python").write(password)
os.popen("sudo reboot").write(password)