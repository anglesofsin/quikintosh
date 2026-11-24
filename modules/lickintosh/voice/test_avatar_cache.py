import asyncio,tempfile,unittest
from avatar_cache import AvatarCache
PNG=b'\x89PNG\r\n\x1a\n'+b'fixture'
URL='https://cdn.discordapp.com/avatars/10/hash.png?size=80'
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
if __name__=='__main__':unittest.main()
