#!/usr/bin/env python3
"""Copy the host PAM policy with absolute host module paths for a Nix PAM client."""
from pathlib import Path
import os,re,sys,json,stat

NAME=re.compile(r'^[A-Za-z0-9_.-]+$')
INCLUDE=re.compile(r'^(\s*-?(?:auth|account|password|session)\s+(?:include|substack)\s+)([\w.-]+)(\s*)$')
AT_INCLUDE=re.compile(r'^(\s*@include\s+)([\w.-]+)(\s*)$')
MODULE=re.compile(r'(?<![/\w.-])(pam_[A-Za-z0-9_-]+\.so)\b')

def build_policies(directory, modules=Path('/usr/lib/security')):
    policies={}
    def copy(name):
        if not NAME.fullmatch(name):raise ValueError('Unsupported PAM policy name')
        target='quickintosh-'+name
        if target in policies:return target
        policies[target]='' # break include cycles while retaining PAM's own stack semantics
        rows=[]
        source=directory/name
        if not source.exists():source=Path('/usr/lib/pam.d')/name
        for line in source.read_text().splitlines():
            body,separator,comment=line.partition('#')
            match=INCLUDE.fullmatch(body) or AT_INCLUDE.fullmatch(body)
            if match:body=match[1]+copy(match[2])+match[3]
            def absolute(match):
                path=modules/match[1]
                return str(path)
            body=MODULE.sub(absolute,body)
            rows.append(body+(separator+comment if separator else ''))
        policies[target]='\n'.join(rows)+'\n'
        return target
    copy('system-auth')
    policies['lickintosh-lock']='# Quickintosh Arch host policy\nauth include quickintosh-system-auth\n'
    # Never submit an empty password to the host password stack in the
    # fingerprint retry loop (this can trigger pam_faillock).
    fingerprint=modules/'pam_fprintd.so'
    policies['lickintosh-lock-fprint']='# Quickintosh Arch host policy\nauth required '+str(fingerprint if fingerprint.exists() else modules/'pam_deny.so')+'\n'
    return policies

def diagnose(directory=Path('/etc/pam.d'),library=Path('/usr/lib/libpam.so.0'),helper=Path('/usr/bin/unix_chkpwd')):
    checks={'host_python':Path('/usr/bin/python3').is_file(),'host_pam':library.is_file(),
            'lock_policy':(directory/'lickintosh-lock').is_file(),'host_system_auth':(directory/'system-auth').is_file()}
    try:
        mode=helper.stat()
        checks['host_password_helper']=mode.st_uid==0 and bool(mode.st_mode & (stat.S_ISUID | stat.S_ISGID)) and os.access(helper,os.X_OK)
    except OSError:checks['host_password_helper']=False
    return {'checks':checks,'ready':all(checks.values()),
            'note':'No authentication attempted. Check journalctl and faillock on this Arch host if a correct password is rejected.'}

def install(directory=Path('/etc/pam.d')):
    policies=build_policies(directory)
    for name,text in policies.items():
        target=directory/name
        if target.exists() and not name.startswith('quickintosh-') and not target.read_text().startswith('# Quickintosh'):
            print('Preserving existing administrator policy:',target);continue
        if target.exists() and target.read_text()==text:continue
        if target.exists():
            backup=target.with_name(target.name+'.quickintosh-backup')
            if not backup.exists():backup.write_bytes(target.read_bytes());backup.chmod(0o600)
        temporary=target.with_name(target.name+'.quickintosh-tmp')
        temporary.write_text(text);temporary.chmod(0o644);temporary.replace(target)
if __name__=='__main__':
    if sys.argv[1:]==['--doctor']:
        result=diagnose();print(json.dumps(result,indent=2));raise SystemExit(0 if result['ready'] else 1)
    if os.geteuid()!=0:raise SystemExit('Run this through sudo bash arch/system-setup.sh')
    install()
