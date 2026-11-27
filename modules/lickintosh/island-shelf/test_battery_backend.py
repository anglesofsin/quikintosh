import unittest
from unittest.mock import patch
from gi.repository import Gio,GLib
from battery_backend import row,inventory,merge
class BatteryTests(unittest.TestCase):
 def test_unknown_and_invalid_charge(self):
  for value in [-1,101,float('nan'),float('inf'),None,'unknown']:
   self.assertIsNone(row('device','Phone',value,False,'phone','KDE Connect'))
 def test_stale_devices_retained_then_expired(self):
  old={'id':'phone','percent':64,'lastSeen':100,'charging':True}
  stale=merge([old],[],200);self.assertFalse(stale[0]['connected']);self.assertFalse(stale[0]['charging'])
  self.assertEqual(merge([old],[],86501),[])
  current=merge([old],[dict(old,percent=80)],200);self.assertEqual(len(current),1);self.assertTrue(current[0]['connected']);self.assertEqual(current[0]['percent'],80)
 def test_known_charge(self):
  self.assertEqual(row('device','Phone',63.7,True,'phone','KDE Connect')['percent'],64)
 @patch('battery_backend.Gio.bus_get_sync')
 def test_missing_buses_are_empty(self,bus):
  bus.side_effect=GLib.Error('Unavailable')
  self.assertEqual(inventory(),{'devices':[],'sources':[]})
 @patch('battery_backend.properties')
 @patch('battery_backend.call')
 @patch('battery_backend.Gio.bus_get_sync')
 def test_upower_and_kdeconnect_inventory(self,bus,call,props):
  call.side_effect=[(['/org/freedesktop/UPower/devices/battery_BAT0'],),(['phone'],)]
  props.side_effect=[{'Type':2,'IsPresent':True,'Model':'Laptop','Percentage':81,'State':1},{'name':'Phone'},{'charge':64,'isCharging':False}]
  result=inventory()['devices'];self.assertEqual([d['percent'] for d in result],[81,64]);self.assertTrue(result[0]['charging']);self.assertEqual(result[1]['source'],'KDE Connect')
if __name__=='__main__':unittest.main()
