#!/usr/bin/env python3
"""Explicit interactive PAM check without locking or recording credentials."""
import getpass
import importlib.util
from pathlib import Path
import sys

path=Path(__file__).with_name('host-pam.py')
spec=importlib.util.spec_from_file_location('quickintosh_host_pam',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result=module.authenticate(getpass.getpass('Quickintosh — account password: '))
if result['success']:
    print('Authentication succeeded. No screen was locked.')
else:
    print('Authentication failed:',result['kind'],'PAM status',result['status'])
    if result['message']:print(result['message'])
    print('Inspect the host PAM journal/account lockout before retrying.')
sys.exit(0 if result['success'] else 1)
