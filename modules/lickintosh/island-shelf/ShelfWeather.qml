import QtQuick
import QtQuick.Layouts
import qs.components
import qs.services
import qs.rosa.services
Rectangle {
 id:root
 signal activated()
 radius:24;color:IslandConfig.s('shelfWidgetCards') ? '#15232e':'#08ffffff'
 border.width:1;border.color:'#12ffffff'
 function icon(code){return WeatherState._iconFor(code)}
 function hour(value,index){if(index===0)return qsTr('Now');const d=new Date(value);return isNaN(d.getTime()) ? String(value).slice(-5):Qt.formatTime(d,'hAP')}
 ColumnLayout{anchors.fill:parent;anchors.margins:14;spacing:5
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:IslandConfig.s('dashboardWeatherLocation') && WeatherState.city ? WeatherState.city:qsTr('Weather');color:'#e7e7eb';font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.DemiBold;elide:Text.ElideRight;textFormat:Text.PlainText}
   ShelfIcon{visible:WeatherState.available && IslandConfig.s('dashboardWeatherLocation');size:12;Layout.preferredWidth:12;Layout.preferredHeight:12;icon:'notch/navigation.svg';color:'#dedee5'}
  }
  RowLayout{Layout.fillWidth:true;spacing:10
   Text{text:WeatherState.available ? Math.round(WeatherState.tempC)+'°':'—°';font.family:ShelfStyle.displayFamily;font.pixelSize:42;font.weight:Font.Light;color:'white'}
   ColumnLayout{Layout.fillWidth:true;spacing:2
    ShelfIcon{Layout.alignment:Qt.AlignRight;size:21;Layout.preferredWidth:21;Layout.preferredHeight:21;visible:WeatherState.available;icon:root.icon(WeatherState.weatherCode);color:'white'}
    Text{Layout.fillWidth:true;text:WeatherState.available ? WeatherState.description:qsTr('Unavailable');horizontalAlignment:Text.AlignRight;elide:Text.ElideRight;font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'#ededf1';textFormat:Text.PlainText}
    Text{Layout.alignment:Qt.AlignRight;visible:WeatherState.forecast.length>0;text:WeatherState.forecast.length ? qsTr('H:%1° L:%2°').arg(WeatherState.forecast[0].tempMax).arg(WeatherState.forecast[0].tempMin):'';font.family:ShelfStyle.textFamily;font.pixelSize:10;color:'#c8c8d0'}
   }
  }
  Item{Layout.fillHeight:true;Layout.minimumHeight:0}
  RowLayout{id:hours;Layout.fillWidth:true;spacing:8
   Repeater{model:WeatherState.hourly.slice(0,4)
    delegate:ColumnLayout{required property var modelData;required property int index;Layout.fillWidth:true;Layout.preferredWidth:(hours.width-24)/4;Layout.horizontalStretchFactor:1;spacing:3
     Text{Layout.alignment:Qt.AlignHCenter;text:root.hour(modelData.time,index);font.family:ShelfStyle.textFamily;font.pixelSize:10;color:'#c0c0c8'}
     ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:16;Layout.preferredWidth:16;Layout.preferredHeight:16;icon:root.icon(modelData.code);color:'white'}
     Text{Layout.alignment:Qt.AlignHCenter;text:Math.round(modelData.temp)+'°';font.family:ShelfStyle.textFamily;font.pixelSize:11;font.weight:Font.Medium;color:'white'}
    }
   }
  }
 }
 TapHandler{onTapped:root.activated()}
}
