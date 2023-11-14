import os
import time
password = os.getenv("PASS")
os.popen("sudo -S %s"%("cd /home/vinted/vintedpy && git pull"), 'w').write(password)
time.sleep(15)
os.popen("sudo -S %s"%("pkill main"), 'w').write(password)
time.sleep(15)
os.popen("sudo -S %s"%("reboot"), 'w').write(password)