"""Check that the Tahoe profile cannot leak GTK or MIME preferences into other rices."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[2]/'modules/lickintosh/desktop-profile.py'
class DesktopProfileTests(unittest.TestCase):
 def test_reversible_profile_and_mode_change(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);tools=home/'bin';tools.mkdir()
   tool=tools/'gsettings';tool.write_text('#!/bin/sh\n[ "$1" = get ] && echo "\x27Adwaita\x27"\nexit 0\n');tool.chmod(0o755)
   for name in ['MacTahoe-Light','MacTahoe-Dark']:
    for version in ['gtk-3.0','gtk-4.0']:
     p=home/'theme/share/themes'/name/version;p.mkdir(parents=True);(p/'gtk.css').write_text('/* fixture */')
   (home/'icons/share/icons/MacTahoe-dark').mkdir(parents=True)
   config=home/'.config';(config/'gtk-3.0').mkdir(parents=True)
   (config/'gtk-3.0/settings.ini').write_text('[Settings]\ngtk-theme-name=Original\n')
   (config/'mimeapps.list').write_text('[Default Applications]\ninode/directory=original.desktop;\nimage/png=original-photos.desktop;\n')
   (config/'gtk-3.0/gtk.css').symlink_to(home/'original.css');(home/'original.css').write_text('original')
   before={p.relative_to(config):p.read_bytes() for p in config.rglob('*') if p.is_file()}
   env={**os.environ,'HOME':d,'PATH':str(tools)+':'+os.environ['PATH']}
   def run(action,*args):subprocess.run(['python3',str(SCRIPT),action,str(home/'theme'),str(home/'icons'),*args],env=env,check=True)
   run('enter');run('enter')
   self.assertIn('MacTahoe-Dark',(config/'gtk-3.0/settings.ini').read_text())
   self.assertIn('lickintosh-finder.desktop',(config/'mimeapps.list').read_text())
   self.assertIn('image/png=lickintosh-quicklook.desktop;',(config/'mimeapps.list').read_text())
   import json
   previous=json.loads((home/'.local/state/lickintosh/desktop-profile/previous-openers.json').read_text());self.assertEqual(previous['image/png'],'original-photos.desktop')
   run('mode','light');self.assertIn('MacTahoe-Light',(config/'gtk-3.0/settings.ini').read_text())
   run('leave');run('leave')
   self.assertEqual(before,{p.relative_to(config):p.read_bytes() for p in config.rglob('*') if p.is_file()})
   self.assertTrue((config/'gtk-3.0/gtk.css').is_symlink())
   self.assertEqual('original',(home/'original.css').read_text())
if __name__=='__main__':unittest.main()
