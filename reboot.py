import os
import time
password = os.getenv("PASS")
os.system("cd /home/vinted/vintedpy && git pull")
time.sleep(15)
os.popen("sudo -S %s"%("pkill -9 python"), 'w').write(password)
time.sleep(15)
os.popen("sudo -S %s"%("reboot"), 'w').write(password)