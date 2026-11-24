import unittest
from bridge import clean,Broker
class BridgeTests(unittest.TestCase):
 def event(self,client='canary',**kwargs):
  return dict(type='voice',version=1,client=client,active=True,participants=[dict(id='10',name='Self',self=True,speaking=True,avatar='https://evil.invalid/avatar')],**kwargs)
 def test_validation(self):
  self.assertIsNone(clean({'type':'MESSAGE_NOTIFICATION'}));self.assertIsNone(clean(self.event('unknown')))
  self.assertEqual(clean(self.event())['participants'][0]['avatar'],'')
 def test_clients_are_isolated(self):
  events=[];b=Broker(events.append);b.update('a',self.event());b.update('b',self.event('stable'))
  self.assertEqual(set(events[-1]['clients']),{'canary','stable'});b.remove('a')
  self.assertEqual(set(events[-1]['clients']),{'stable'});b.remove('b');self.assertEqual(events[-1]['clients'],{})
 def test_reconnect_cleanup(self):
  events=[];b=Broker(events.append);b.update('old',self.event());b.update('new',self.event(channel='New'))
  b.remove('old');self.assertEqual(events[-1]['clients']['canary']['channel'],'New')
 def test_bad_participants(self):
  v=self.event();v['participants']=[{'id':'bad'},None];self.assertEqual(clean(v)['participants'],[])
 def test_privacy_flag(self): self.assertTrue(clean(self.event(streamer=True))['streamer'])
if __name__=='__main__': unittest.main()

class ExternalFallbackTests(unittest.TestCase):
 def test_native_metadata_wins_and_fallback_recovers_disconnect(self):
  values=[];broker=Broker(values.append)
  broker.external={'canary':dict(client='canary',active=True,channel='Discord Canary call',participants=[],external=True)}
  broker.publish();self.assertTrue(values[-1]['clients']['canary']['external'])
  broker.update('client',dict(type='voice',version=1,client='canary',active=True,channel='Actual server',participants=[]))
  self.assertEqual(values[-1]['clients']['canary']['channel'],'Actual server')
  broker.remove('client');self.assertTrue(values[-1]['clients']['canary']['external'])
