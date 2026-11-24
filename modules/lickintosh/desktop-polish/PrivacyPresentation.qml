pragma Singleton
import QtQuick
import Quickshell
Singleton {
 id:root
 property var corner:({})
 function setCorner(screen,show){
  if(!!corner[screen]===!!show)return
  const next=Object.assign({},corner)
  if(show)next[screen]=true
  else delete next[screen]
  corner=next
 }
}
