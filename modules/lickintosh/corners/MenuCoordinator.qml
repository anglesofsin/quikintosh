pragma Singleton
import QtQuick
import Quickshell
Singleton{
 id:root
 property var owner:null
 signal opening()
 function close(){const previous=owner;owner=null;if(previous)previous.closeMenus()}
 function claim(item){if(owner!==item){close();owner=item}opening()}
 function release(item){if(owner===item)owner=null}
}
