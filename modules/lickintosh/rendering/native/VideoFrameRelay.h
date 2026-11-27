#pragma once
#include <QObject>
#include <QPointer>
#include <QVideoSink>
#include <QVideoFrame>
#include <QElapsedTimer>
#include <QVariantMap>
#include <QVideoFrameFormat>
#include <array>
#include <algorithm>
#include <memory>
#include <mutex>
#include <QThread>
#include <QtQml/qqmlregistration.h>

// Forward implicitly shared frames: one decoder and one playback clock.
class VideoFrameRelay : public QObject {
 Q_OBJECT
 QML_ELEMENT
 Q_PROPERTY(bool measuring READ isMeasuring WRITE setMeasuring)
 Q_PROPERTY(bool hasFrame READ hasFrame NOTIFY hasFrameChanged)
 Q_PROPERTY(QVideoSink* source READ source WRITE setSource NOTIFY sourceChanged)
 Q_PROPERTY(QVideoSink* destination READ destination WRITE setDestination NOTIFY destinationChanged)
public:
 Q_INVOKABLE QVariantMap statistics() const {
  auto sorted=gaps;std::sort(sorted.begin(),sorted.begin()+gapCount);
  const auto frame=input ? input->videoFrame():QVideoFrame();const auto format=frame.surfaceFormat();
  quint64 coalesced=0;{std::lock_guard lock(mailbox->mutex);coalesced=mailbox->coalesced;}
  return {{"frames",double(frames)},{"coalescedFrames",double(coalesced)},{"maxGapMs",double(maxGap)},{"stallsOver100ms",double(stalls)},{"lastGapMs",double(lastGap)},
   {"lastFrameAgoMs",lastFrame<0 ? -1.0:double(clock.elapsed()-lastFrame)},
   {"fps",frames>1 && lastFrame>firstFrame ? double(frames-1)*1000/(lastFrame-firstFrame):0},
   {"p95GapMs",gapCount ? double(sorted[std::min(gapCount-1,int(gapCount*.95))]):0},
   {"width",format.frameWidth()},{"height",format.frameHeight()},
   {"pixelFormat",QVideoFrameFormat::pixelFormatToString(format.pixelFormat())},
   {"frameStorage",!frame.isValid() ? "unavailable":frame.handleType()==QVideoFrame::RhiTextureHandle ? "gpu-texture":"cpu-memory"}};
 }
 using QObject::QObject;
 ~VideoFrameRelay() override {disconnect(connection);disconnect(destruction);invalidateMailbox(true);}
 bool hasFrame() const { return validFrame; }
 bool isMeasuring() const {return measuring;}
 void setMeasuring(bool value){if(measuring==value)return;measuring=value;resetStatistics();std::lock_guard lock(mailbox->mutex);mailbox->measuring=value;mailbox->coalesced=0;}
 QVideoSink* source() const { return input; }
 QVideoSink* destination() const { return output; }
 void setSource(QVideoSink* value) {
  if (input == value) return;
  disconnect(connection);disconnect(destruction);
  const auto generation=invalidateMailbox(false);
  input = value;
  const auto box=mailbox;
  if (input) connection = connect(input, &QVideoSink::videoFrameChanged, this,
   [box,generation](const QVideoFrame& frame) {
    QVideoFrame previous;VideoFrameRelay* receiver=nullptr;
    {
     std::lock_guard lock(box->mutex);
     if(!box->receiver || box->generation!=generation)return;
     receiver=box->receiver;
     if(QThread::currentThread()!=receiver->thread()){
      if(box->hasPending && box->measuring)box->coalesced++;
      previous.swap(box->latest);box->latest=frame;box->hasPending=true;
      if(box->scheduled)return;
      box->scheduled=true;
      QMetaObject::invokeMethod(receiver,[box,generation]{
       QVideoFrame latest;VideoFrameRelay* current=nullptr;
       {
        std::lock_guard lock(box->mutex);
        if(!box->receiver || box->generation!=generation)return;
        box->scheduled=false;
        if(!box->hasPending)return;
        box->hasPending=false;latest.swap(box->latest);current=box->receiver;
       }
       current->deliver(latest);
      },Qt::QueuedConnection);
      return;
     }
     // An immediate GUI-thread frame supersedes an older queued frame too.
     previous.swap(box->latest);box->hasPending=false;
    }
    receiver->deliver(frame);
   },Qt::DirectConnection);
  if(input)destruction=connect(input,&QObject::destroyed,this,[this,generation]{
   {std::lock_guard lock(mailbox->mutex);if(mailbox->generation!=generation)return;}
   input=nullptr;invalidateMailbox(false);deliver(QVideoFrame());emit sourceChanged();
  });
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
 struct Mailbox {
  explicit Mailbox(VideoFrameRelay* target):receiver(target){}
  std::mutex mutex;
  VideoFrameRelay* receiver;
  QVideoFrame latest;
  quint64 generation=0,coalesced=0;
  bool scheduled=false,hasPending=false,measuring=false;
 };
 std::shared_ptr<Mailbox> mailbox=std::make_shared<Mailbox>(this);
 quint64 invalidateMailbox(bool destroyed){
  QVideoFrame previous;quint64 generation;
  {std::lock_guard lock(mailbox->mutex);generation=++mailbox->generation;previous.swap(mailbox->latest);mailbox->scheduled=false;mailbox->hasPending=false;if(destroyed)mailbox->receiver=nullptr;}
  return generation;
 }
 void deliver(const QVideoFrame& frame) {
  if(measuring && frame.isValid()){
   if(!clock.isValid())clock.start();
   const auto now=clock.elapsed();
   if(lastFrame>=0){lastGap=now-lastFrame;maxGap=qMax(maxGap,lastGap);if(lastGap>100)stalls++;gaps[gapIndex++%gaps.size()]=lastGap;gapCount=std::min(gapCount+1,int(gaps.size()));}
   else firstFrame=now;
   lastFrame=now;frames++;
  }

  QPointer<VideoFrameRelay> guard(this);
  if(output && output!=input)output->setVideoFrame(frame);
  if(!guard)return;
  const bool valid=frame.isValid();
  if(validFrame!=valid){validFrame=valid;emit hasFrameChanged();}
 }
 void prime() { if(input)deliver(input->videoFrame()); }
 void resetStatistics(){clock.invalidate();firstFrame=lastFrame=-1;frames=maxGap=stalls=lastGap=0;gapCount=gapIndex=0;}
 bool measuring=false;
 QElapsedTimer clock;
 qint64 frames=0,firstFrame=-1,lastFrame=-1,maxGap=0,stalls=0,lastGap=0;
 std::array<qint64,120> gaps{};
 int gapCount=0;size_t gapIndex=0;
 bool validFrame=false;
 QPointer<QVideoSink> input, output;
 QMetaObject::Connection connection, destruction;
};
