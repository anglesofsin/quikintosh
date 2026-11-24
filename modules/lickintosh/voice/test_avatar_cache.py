import asyncio,tempfile,unittest
from avatar_cache import AvatarCache,normalize_image
PNG=b'\x89PNG\r\n\x1a\n'+b'fixture'
URL='https://cdn.discordapp.com/avatars/10/hash.png?size=128'
class CacheTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):self.directory=tempfile.TemporaryDirectory();self.caches=[]
 async def asyncTearDown(self):
  tasks=[task for c in self.caches for task in c.tasks.values()]
  for task in tasks:task.cancel()
  await asyncio.gather(*tasks,return_exceptions=True)
  self.directory.cleanup()
 def cache(self,fetch):
  c=AvatarCache(lambda:None,self.directory.name,fetch);self.caches.append(c);return c
 async def loaded(self,c):await asyncio.gather(*list(c.tasks.values()))
 async def test_persisted_image_needs_no_network_after_restart(self):
  c=self.cache(lambda url:PNG);self.assertEqual(c.image(URL),'');await self.loaded(c)
  def offline(url):self.fail('Cached image attempted a download')
  restarted=self.cache(offline);self.assertTrue(restarted.image(URL).startswith('file:'));self.assertFalse(restarted.tasks)
 async def test_new_hash_retains_previous_photo_while_offline(self):
  c=self.cache(lambda url:PNG);c.image(URL);await self.loaded(c)
  def offline(url):raise ConnectionError('offline')
  c.fetch=offline
  photo=c.image(URL.replace('/hash.png','/newhash.png'))
  self.assertTrue(photo.endswith('.last.png'));self.assertTrue(c.paths(URL)[1].exists())
 async def test_only_discord_images_are_downloaded(self):
  c=self.cache(lambda url:self.fail('Invalid URL reached downloader'))
  self.assertEqual(c.image('http://127.0.0.1/private'),'');self.assertEqual(c.image('https://evil.invalid/a.png'),'');self.assertFalse(c.tasks)
class NormalizationTests(unittest.TestCase):
 def test_all_discord_renditions_share_canonical_cache_key(self):
  for ext in ['webp','gif','png','jpeg']:
   self.assertEqual(normalize_image('https://cdn.discordapp.com/avatars/10/hash.'+ext+'?size=128'),URL)
 def test_default_avatar_is_supported(self):
  self.assertEqual(normalize_image('https://cdn.discordapp.com/embed/avatars/2.png'),'https://cdn.discordapp.com/embed/avatars/2.png?size=128')
 def test_credentials_ports_and_redirect_hosts_rejected(self):
  for url in ['https://cdn.discordapp.com.evil/avatars/10/hash.png','https://x@cdn.discordapp.com/avatars/10/hash.png','https://cdn.discordapp.com:443/avatars/10/hash.png']:
   self.assertEqual(normalize_image(url),'')
if __name__=='__main__':unittest.main()
