import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

scale=load('interface_scale',ROOT/'modules/lickintosh/interface-scale.py')
auth=load('arch_host_pam',ROOT/'modules/lickintosh/arch-pam.py')

class InterfaceScale(unittest.TestCase):
    def test_safe_default_and_allowed_values(self):
        with tempfile.TemporaryDirectory() as home:
            p=Path(home)/'.config/lickintosh/shell-config.json'
            self.assertEqual(scale.read_scale(home),1)
            p.parent.mkdir(parents=True)
            for value,expected in [(1.25,1.25),(.75,.75),(2,2),(0,1),(-1,1),(100,1),(True,1),('NaN',1),('$(touch /tmp/not-run)',1)]:
                p.write_text(json.dumps({'general':{'shellScale':value}}))
                self.assertEqual(scale.read_scale(home),expected)
            p.write_text('{broken')
            self.assertEqual(scale.read_scale(home),1)

class Portuguese(unittest.TestCase):
    def test_core_labels_and_placeholders(self):
        table=dict(line.split('|',1) for line in (ROOT/'modules/lickintosh/i18n/pt-BR.txt').read_text().splitlines() if '|' in line)
        for english in ['Settings','Language & Region','Shell Scale','Wrong Password','Control Center','Notifications','Dynamic Island','Wallpaper','Copy','Move to Trash']:
            self.assertIn(english,table)
            self.assertNotEqual(table[english],english)
        for value in table.values():
            self.assertTrue(value.strip())

class HostPam(unittest.TestCase):
    @unittest.skipIf(os.getuid()==0,'Production authenticator refuses root')
    def test_missing_policy_fails_closed(self):
        with self.assertRaises(RuntimeError):
            auth.authenticate('not-a-password',service='quickintosh-nonexistent-fixture')

    @unittest.skipIf(os.getuid()==0,'Production authenticator refuses root')
    def test_isolated_real_pam_permit_and_deny(self):
        library=os.environ.get('QUICKINTOSH_TEST_PAM_LIBRARY')
        if not library:self.skipTest('Set QUICKINTOSH_TEST_PAM_LIBRARY for an isolated real PAM stack test')
        base=Path(library).parent
        with tempfile.TemporaryDirectory() as directory:
            for service,module,success in [('accept','pam_permit.so',True),('reject','pam_deny.so',False)]:
                (Path(directory)/service).write_text('auth required '+str(base/'security'/module)+'\n')
                result=auth.authenticate('fixture-only',service,library,directory)
                self.assertEqual(result['success'],success)
                self.assertEqual(result['kind'],'success' if success else 'rejected')

if __name__=='__main__':unittest.main()
