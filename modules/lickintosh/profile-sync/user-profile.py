"""Read fallback identity without changing the system account or other rices."""
import json,os,pwd
from pathlib import Path
user=pwd.getpwuid(os.getuid());home=Path.home()
avatar=next((str(path) for path in [home/'.face',home/'.face.icon',Path('/var/lib/AccountsService/icons')/user.pw_name] if path.is_file() and os.access(path,os.R_OK)),'')
print(json.dumps({'name':user.pw_gecos.split(',')[0] or user.pw_name,'avatar':avatar}))
