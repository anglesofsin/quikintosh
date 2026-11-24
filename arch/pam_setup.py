#!/usr/bin/env python3
"""Copy the host PAM policy with absolute host module paths for a Nix PAM client."""
from pathlib import Path
import os,re,sys

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
    policies['lickintosh-lock']=policies['lickintosh-lock-fprint']='# Quickintosh Arch host policy\n'+''.join(kind+' include quickintosh-system-auth\n' for kind in ['auth','account','password','session'])
    return policies

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
    if os.geteuid()!=0:raise SystemExit('Run this through sudo bash arch/system-setup.sh')
    install()
