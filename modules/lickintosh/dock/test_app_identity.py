import tempfile
from pathlib import Path
import unittest
from app_identity import discord_key,ProcessIdentities

class Identities(unittest.TestCase):
 def test_channels_do_not_collapse(self):
  for value,key in [('.Discord-wrapped','discord'),('.DiscordCanary-wrapped','discord-canary'),('discord-ptb','discord-ptb'),('com.discordapp.DiscordCanary','discord-canary'),('equibop','equibop')]:
   self.assertEqual(discord_key(value),key)
  self.assertEqual(discord_key('notdiscord'),'')
 def test_process_cache_handles_pid_reuse(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);p=root/'123';p.mkdir();stable=root/'Discord';stable.touch();canary=root/'DiscordCanary';canary.touch()
   def setup(exe,start):
    (p/'stat').write_text('123 (Discord process) '+' '.join(['S']+['0']*18+[str(start)]))
    (p/'cmdline').write_bytes(str(exe).encode()+b'\0');(p/'exe').unlink(missing_ok=True);(p/'exe').symlink_to(exe)
   resolver=ProcessIdentities(root);setup(stable,1);self.assertEqual(resolver.resolve(123),'discord')
   setup(canary,2);self.assertEqual(resolver.resolve(123),'discord-canary')
   self.assertEqual(resolver.resolve(456),'')
if __name__=='__main__':unittest.main()
