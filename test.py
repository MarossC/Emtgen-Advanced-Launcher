import os, re

for name in os.listdir("."):
    if re.match(r'emt',name,flags=re.IGNORECASE):
        print(name)
