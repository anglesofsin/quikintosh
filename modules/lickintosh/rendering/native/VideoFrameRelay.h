#pragma once
#include <QObject>
#include <QPointer>
#include <QVideoSink>
#include <QVideoFrame>
#include <QElapsedTimer>
#include <QVariantMap>
#include <QtQml/qqmlregistration.h>

// Forward implicitly shared frames: one decoder and one playback clock.
class VideoFrameRelay : public QObject {
 Q_OBJECT
 QML_ELEMENT
 Q_PROPERTY(bool measuring MEMBER measuring)
 Q_PROPERTY(bool hasFrame READ hasFrame NOTIFY hasFrameChanged)
 Q_PROPERTY(QVideoSink* source READ source WRITE setSource NOTIFY sourceChanged)
 Q_PROPERTY(QVideoSink* destination READ destination WRITE setDestination NOTIFY destinationChanged)
public:
 Q_INVOKABLE QVariantMap statistics() const {return {{"frames",double(frames)},{"maxGapMs",double(maxGap)},{"stallsOver100ms",double(stalls)},{"lastGapMs",double(lastGap)},{"lastFrameAgoMs",lastFrame<0 ? -1.0:double(clock.elapsed()-lastFrame)}};}
 using QObject::QObject;
 bool hasFrame() const { return validFrame; }
 QVideoSink* source() const { return input; }
 QVideoSink* destination() const { return output; }
 void setSource(QVideoSink* value) {
  if (input == value) return;
  disconnect(connection);disconnect(destruction);
  input = value;
  if (input) connection = connect(input, &QVideoSink::videoFrameChanged, this,
   [this] { if(input)deliver(input->videoFrame()); });
  if(input)destruction=connect(input,&QObject::destroyed,this,[this]{input=nullptr;deliver(QVideoFrame());emit sourceChanged();});
  if(!input)deliver(QVideoFrame());
  prime(); emit sourceChanged();
 }
 void setDestination(QVideoSink* value) {
  if (output == value) return;
  output = value; prime(); emit destinationChanged();
 }
signals:
 void hasFrameChanged();
 void sourceChanged();
 void destinationChanged();
private:
 void deliver(const QVideoFrame& frame) {
  if(measuring && frame.isValid()){
   if(!clock.isValid())clock.start();
   const auto now=clock.elapsed();
   if(lastFrame>=0){lastGap=now-lastFrame;maxGap=qMax(maxGap,lastGap);if(lastGap>100)stalls++;}
   lastFrame=now;frames++;
  }else if(!measuring){lastFrame=-1;frames=0;maxGap=0;stalls=0;lastGap=0;}

  if(output && output!=input)output->setVideoFrame(frame);
  const bool valid=frame.isValid();
  if(validFrame!=valid){validFrame=valid;emit hasFrameChanged();}
 }
 void prime() { if(input)deliver(input->videoFrame()); }
 bool measuring=false;
 QElapsedTimer clock;
 qint64 frames=0,lastFrame=-1,maxGap=0,stalls=0,lastGap=0;
 bool validFrame=false;
 QPointer<QVideoSink> input, output;
 QMetaObject::Connection connection, destruction;
};
