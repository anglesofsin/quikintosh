import QtQuick
import QtQuick.Layouts
import qs.services
Item{
 id:root
 default property alias content:body.data
 property string title:''
 Layout.fillWidth:true
 implicitHeight:heading.implicitHeight+body.implicitHeight+38
 Text{id:heading;x:4;y:0;text:I18n.tr(root.title);color:Theme.textSecondary;font.family:'SF Pro Display';font.pixelSize:12;font.weight:Font.DemiBold}
 Rectangle{x:0;y:heading.implicitHeight+10;width:parent.width;height:body.implicitHeight+24;radius:16;color:Theme.isLight ? '#f5ffffff':'#f52d2d32';border.width:1;border.color:Theme.isLight ? '#14000000':'#16ffffff'}
 ColumnLayout{id:body;x:16;y:heading.implicitHeight+22;width:parent.width-32;spacing:8}
}
