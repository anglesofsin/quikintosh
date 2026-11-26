#include "VideoFrameRelay.h"
#include <QGuiApplication>
#include <QDebug>
#include <cstdio>
#include <QVideoFrameFormat>
int main(int argc, char** argv) {
 qputenv("QT_QPA_PLATFORM","offscreen");
 QGuiApplication app(argc,argv);
 QVideoSink source, target, replacement;
 VideoFrameRelay relay;
 relay.setSource(&source);relay.setDestination(&target);
 for (int i=0;i<120;++i) {
  QVideoFrame frame(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));
  frame.setStartTime(i*16667);
  source.setVideoFrame(frame);
  if (!target.videoFrame().isValid() || target.videoFrame().startTime()!=frame.startTime()) {fprintf(stderr,"frame mismatch i=%d valid=%d target=%d time=%lld sourceTime=%lld\n",i,frame.isValid(),target.videoFrame().isValid(),(long long)target.videoFrame().startTime(),(long long)source.videoFrame().startTime());return 1;}
 }
 relay.setDestination(&replacement);
 if (replacement.videoFrame().startTime()!=source.videoFrame().startTime()) {qWarning()<<"destination replacement";return 2;}
 relay.setSource(nullptr);
 source.setVideoFrame(QVideoFrame());
 if (replacement.videoFrame().isValid() || relay.hasFrame()) {qWarning()<<"detachment";return 3;}
 auto temporary = new QVideoSink;
 relay.setSource(temporary);delete temporary;
 if(relay.source()!=nullptr || relay.hasFrame()){qWarning()<<"source destruction";return 4;}
 relay.setDestination(nullptr);
 return 0;
}
