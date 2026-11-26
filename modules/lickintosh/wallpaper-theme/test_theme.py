import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('wallpaper_theme',Path(__file__).parents[1]/'wallpaper_theme.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ThemeTests(unittest.TestCase):
 def test_opt_in_cache_disable(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);home=root/'home';theme=root/'theme';icons=root/'icons'
   for mode in ['Dark','Light']:
    for version in ['gtk-3.0','gtk-4.0']:m.write(theme/'share/themes'/('MacTahoe-'+mode)/version/'gtk.css','/* base */')
    base=icons/'share/icons'/('MacTahoe-'+mode.lower());m.write(base/'index.theme','[Icon Theme]\nName=Original\nDirectories=places/scalable\n[places/scalable]\nSize=64\nType=Scalable\nContext=Places\n')
    m.write(base/'places/scalable/folder.svg','<svg xmlns="http://www.w3.org/2000/svg"><path fill="#67b1de" d="M0 0"/><path fill="#fff" d="M1 1"/></svg>')
   c={k:'#aa4477' for k in ['primary','on_primary','surface','on_surface','surface_container','surface_container_low','surface_container_high','surface_container_highest','outline_variant']};palette={'dark':c,'light':c}
   off=m.prepare(home,theme,icons,'dark',{},palette);self.assertFalse(off['gtkEnabled']);self.assertFalse(off['iconsEnabled'])
   on=m.prepare(home,theme,icons,'dark',{'wallpaperGtk':True,'wallpaperFileIcons':True},palette)
   self.assertTrue(on['gtkEnabled']);self.assertTrue(on['iconsEnabled']);self.assertIn('folder',on['icons'])
   svg=Path(on['icons']['folder']).read_text();self.assertNotIn('#67b1de',svg);self.assertIn('#fff',svg);self.assertTrue(svg.startswith('<svg xmlns='));self.assertNotIn('ns0:',svg)
   css=home/'.local/share/themes'/on['gtkTheme']/'gtk-4.0/gtk.css';stamp=css.stat().st_mtime_ns
   same=m.prepare(home,theme,icons,'dark',{'wallpaperGtk':True,'wallpaperFileIcons':True},palette);self.assertEqual(same['gtkTheme'],on['gtkTheme']);self.assertEqual(stamp,css.stat().st_mtime_ns)
   light=m.prepare(home,theme,icons,'light',{'wallpaperGtk':True,'wallpaperFileIcons':True},palette);self.assertNotEqual(light['gtkTheme'],on['gtkTheme'])
   off=m.prepare(home,theme,icons,'dark',{},palette);self.assertEqual(off['gtkTheme'],'MacTahoe-Dark');self.assertEqual(off['iconTheme'],'MacTahoe-dark');self.assertEqual(off['icons'],{})
 def test_hardcoded_accent_overrides(self):
  text='row:selected { color: #0088FF; padding: 12px; } button { background: alpha(#0088ff,.2); }'
  css=m.gtk_accent_overrides(text);self.assertNotIn('#0088',css);self.assertIn('@accent_bg_color',css);self.assertNotIn('padding',css)
 def test_invalid_palette_falls_back(self):
  with tempfile.TemporaryDirectory() as temp:
   r=m.prepare(temp,temp,temp,'dark',{'wallpaperGtk':True,'wallpaperFileIcons':True},{'dark':{'primary':'bad'}});self.assertFalse(r['gtkEnabled']);self.assertFalse(r['iconsEnabled'])
 def test_neutral_and_badge_colors_preserved(self):
  text='<svg><path fill="#fff"/><path fill="#ff0000"/><path fill="#67b1de"/></svg>'
  changed=m.recolor_svg(text,'#cc5599');self.assertIn('#fff',changed);self.assertIn('#ff0000',changed);self.assertNotIn('#67b1de',changed)
if __name__=='__main__':unittest.main()
