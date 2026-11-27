#include "VideoFrameRelay.h"
#include <QGuiApplication>
#include <QDebug>
#include <cstdio>
#include <QVideoFrameFormat>
#include <thread>
int main(int argc, char** argv) {
 qputenv("QT_QPA_PLATFORM","offscreen");
 QGuiApplication app(argc,argv);
 QVideoSink source, target, replacement;
 VideoFrameRelay relay;
 relay.setSource(&source);relay.setDestination(&target);relay.setMeasuring(true);
 for (int i=0;i<120;++i) {
  QVideoFrame frame(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));
  frame.setStartTime(i*16667);
  source.setVideoFrame(frame);
  if (!target.videoFrame().isValid() || target.videoFrame().startTime()!=frame.startTime()) {fprintf(stderr,"frame mismatch i=%d valid=%d target=%d time=%lld sourceTime=%lld\n",i,frame.isValid(),target.videoFrame().isValid(),(long long)target.videoFrame().startTime(),(long long)source.videoFrame().startTime());return 1;}
 }
 auto stats=relay.statistics();
 if(stats["frames"].toInt()!=120 || stats["width"].toInt()!=2 || stats["frameStorage"].toString()!="cpu-memory"){qWarning()<<"frame statistics"<<stats;return 5;}
 relay.setMeasuring(false);
 if(relay.statistics()["frames"].toInt()!=0){qWarning()<<"statistics reset";return 6;}
 relay.setDestination(&replacement);
 if (replacement.videoFrame().startTime()!=source.videoFrame().startTime()) {qWarning()<<"destination replacement";return 2;}
 relay.setSource(nullptr);
 source.setVideoFrame(QVideoFrame());
 if (replacement.videoFrame().isValid() || relay.hasFrame()) {qWarning()<<"detachment";return 3;}
 auto temporary = new QVideoSink;
 relay.setSource(temporary);delete temporary;
 if(relay.source()!=nullptr || relay.hasFrame()){qWarning()<<"source destruction";return 4;}
 relay.setDestination(nullptr);
 // A blocked GUI must receive only the newest worker frame, not a backlog.
 QVideoSink threadedSource, threadedTarget, nextSource;
 VideoFrameRelay threadedRelay;
 threadedRelay.setSource(&threadedSource);threadedRelay.setDestination(&threadedTarget);threadedRelay.setMeasuring(true);
 int delivered=0;
 QObject::connect(&threadedTarget,&QVideoSink::videoFrameChanged,&app,[&]{delivered++;});
 std::thread producer([&]{
  for(int i=0;i<180;++i){QVideoFrame frame(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));frame.setStartTime(i*16667);threadedSource.setVideoFrame(frame);}
 });producer.join();
 if(delivered!=0){qWarning()<<"worker delivered outside GUI";return 7;}
 QCoreApplication::processEvents();
 if(delivered!=1 || threadedTarget.videoFrame().startTime()!=179*16667 || threadedRelay.statistics()["coalescedFrames"].toInt()!=179){qWarning()<<"unbounded/stale frame delivery"<<delivered<<threadedRelay.statistics();return 8;}
 std::thread pending([&]{QVideoFrame frame(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));frame.setStartTime(9000000);threadedSource.setVideoFrame(frame);});pending.join();
 threadedRelay.setSource(&nextSource);
 QVideoFrame fresh(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));fresh.setStartTime(123);nextSource.setVideoFrame(fresh);
 QCoreApplication::processEvents();
 if(threadedTarget.videoFrame().startTime()!=123){qWarning()<<"old source rewound new source";return 9;}
 for(int i=0;i<20;++i){
  auto *doomed=new VideoFrameRelay;doomed->setSource(&threadedSource);doomed->setDestination(&threadedTarget);
  std::thread race([&]{for(int n=0;n<100;++n){QVideoFrame frame(QVideoFrameFormat(QSize(2,2),QVideoFrameFormat::Format_RGBA8888));threadedSource.setVideoFrame(frame);}});
  delete doomed;race.join();QCoreApplication::processEvents();
 }
 return 0;
}
