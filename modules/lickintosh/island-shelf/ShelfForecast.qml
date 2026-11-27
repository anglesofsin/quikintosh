import QtQuick
import QtQuick.Layouts
import qs.services
import qs.rosa.services
Item{
 id:root
 ColumnLayout{anchors.fill:parent;spacing:14
  ShelfWeather{Layout.fillWidth:true;Layout.preferredHeight:170}
  Rectangle{Layout.fillWidth:true;implicitHeight:1;color:ShelfStyle.separator}
  RowLayout{Layout.fillWidth:true;spacing:6
   Repeater{model:WeatherState.forecast.slice(0,7)
    delegate:ColumnLayout{required property var modelData;Layout.fillWidth:true;Layout.preferredWidth:60;spacing:7
     Text{Layout.alignment:Qt.AlignHCenter;text:Qt.formatDate(new Date(modelData.date+'T12:00:00'),'ddd');font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;color:ShelfStyle.secondary}
     ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:22;Layout.preferredWidth:22;Layout.preferredHeight:22;icon:WeatherState._iconFor(modelData.code)}
     Text{Layout.alignment:Qt.AlignHCenter;text:modelData.tempMax+'°';font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;font.weight:Font.DemiBold;color:ShelfStyle.primary}
     Text{Layout.alignment:Qt.AlignHCenter;text:modelData.tempMin+'°';font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;color:ShelfStyle.secondary}
    }
   }
  }
 }
}
