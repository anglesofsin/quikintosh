#include "FramePacer.h"
#include <QGuiApplication>
#include <QQuickWindow>
#include <QScreen>
#include <QTimer>
#include <QEvent>
#include <QLocalSocket>
#include <QJsonDocument>
#include <QJsonObject>
#include <QDateTime>
#include <QChronoTimer>
#include <QSocketNotifier>
#include <QUuid>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstring>
#include <algorithm>
#include <array>
#include <chrono>
#include <mutex>
#include <thread>
#include <vector>
using Clock=std::chrono::steady_clock;
struct FramePolicy {std::atomic<int> fps{0};std::atomic<bool> measuring{false},stopping{false};};
struct WindowFrames {
 int id=0;
 QString role="interface";
 std::mutex mutex;
 std::array<double,240> intervals{};
 size_t size=0,index=0;
 Clock::time_point lastFrame{},deadline{};
 int lastLimit=0;
};
FramePacer::FramePacer(QObject *parent):QObject(parent),policy(std::make_shared<FramePolicy>()) {
 qGuiApp->installEventFilter(this);
 motionTimer=new QChronoTimer(this);motionTimer->setTimerType(Qt::PreciseTimer);connect(motionTimer,&QChronoTimer::timeout,this,&FramePacer::requestGeometry);
 geometrySocket=new QLocalSocket(this);geometryTimeout=new QTimer(this);geometryTimeout->setSingleShot(true);geometryTimeout->setInterval(150);
 connect(geometrySocket,&QLocalSocket::connected,this,[this]{geometrySocket->write("j/quickintosh:geometry");geometrySocket->flush();});
 connect(geometrySocket,&QLocalSocket::readyRead,this,[this]{geometryReply+=geometrySocket->readAll();if(geometryReply.size()>1024*1024)geometrySocket->abort();});
 connect(geometrySocket,&QLocalSocket::disconnected,this,[this]{
  geometryTimeout->stop();geometryReply+=geometrySocket->readAll();
  consumeGeometry(geometryReply,false);
 });
 connect(geometryTimeout,&QTimer::timeout,this,[this]{if(frameSynchronized()){geometrySocket->abort();return;}nextGeometryAttempt=QDateTime::currentMSecsSinceEpoch()+2000;geometrySocket->abort();if(hasGeometry){hasGeometry=false;renderedGeometry.clear();emit geometryChanged();}});
 connect(geometrySocket,&QLocalSocket::errorOccurred,this,[this](auto){if(frameSynchronized()){geometryTimeout->stop();return;}nextGeometryAttempt=QDateTime::currentMSecsSinceEpoch()+2000;geometryTimeout->stop();nativeAnimating=false;if(hasGeometry){hasGeometry=false;renderedGeometry.clear();emit geometryChanged();}updateGeometryTimer();});
 QTimer::singleShot(0,this,[this]{for(auto *w:QGuiApplication::allWindows())attach(qobject_cast<QQuickWindow *>(w));});
}
FramePacer::~FramePacer(){if(frameNotifier)frameNotifier->setEnabled(false);if(frameFd>=0)close(frameFd);if(!framePath.isEmpty())unlink(framePath.constData());policy->stopping=true;qGuiApp->removeEventFilter(this);}
int FramePacer::maximumFps()const{return policy->fps;}
void FramePacer::setMaximumFps(int value){value=std::clamp(value,0,1000);if(policy->fps.exchange(value)!=value)emit maximumFpsChanged();}
bool FramePacer::measuring()const{return policy->measuring;}
void FramePacer::setMeasuring(bool value){if(policy->measuring.exchange(value)!=value)emit measuringChanged();}
bool FramePacer::eventFilter(QObject *object,QEvent *event){
 if(event->type()==QEvent::Show || event->type()==QEvent::PlatformSurface)attach(qobject_cast<QQuickWindow *>(object));
 return false;
}
void FramePacer::attach(QQuickWindow *window){
 if(!window || windows.contains(window))return;
 static int nextId=0;
 window->setPersistentGraphics(keepPrepared);window->setPersistentSceneGraph(keepPrepared);
 auto state=std::make_shared<WindowFrames>();state->id=++nextId;windows.insert(window,state);
 const auto shared=policy;
 // Render-thread pacing, never a GUI/QML timer pretending to limit rendering.
 // Zero leaves the renderer/vsync untouched; no clock/mutex/sleep in that path.
 connect(window,&QQuickWindow::beforeFrameBegin,window,[shared,state]{
  if(shared->stopping.load(std::memory_order_relaxed))return;
  const int fps=shared->fps.load(std::memory_order_relaxed);
  if(fps<=0){state->lastLimit=0;return;}
  const auto now=Clock::now();const auto period=std::chrono::nanoseconds(1000000000LL/fps);
  if(state->lastLimit!=fps || state->deadline<now-4*period){state->deadline=now;state->lastLimit=fps;}
  if(state->deadline>now)std::this_thread::sleep_until(state->deadline);
  state->deadline=Clock::now()+period;
 },Qt::DirectConnection);
 connect(window,&QQuickWindow::frameSwapped,window,[shared,state]{
  if(!shared->measuring.load(std::memory_order_relaxed) || shared->stopping)return;
  const auto now=Clock::now();std::lock_guard guard(state->mutex);
  if(state->lastFrame!=Clock::time_point{}){
   const double ms=std::chrono::duration<double,std::milli>(now-state->lastFrame).count();
   if(ms<500){state->intervals[state->index]=ms;state->index=(state->index+1)%state->intervals.size();state->size=std::min(state->size+1,state->intervals.size());}
   else{state->size=0;state->index=0;}
  }
  state->lastFrame=now;
 },Qt::DirectConnection);
 connect(window,&QObject::destroyed,this,[this,window]{windows.remove(window);});
}
void FramePacer::setGeometryMotion(bool active,int fps){motionRequested=active;geometryLimit=std::clamp(fps,0,1000);updateGeometryTimer();if(active)requestGeometry();}
void FramePacer::updateGeometryTimer(){
 if(!motionRequested && !nativeAnimating){motionTimer->stop();return;}
 const double refresh=reportedRefresh>0 ? reportedRefresh:(qGuiApp->primaryScreen() ? qGuiApp->primaryScreen()->refreshRate():60);
 const double target=frameSynchronized() ? 2:(geometryLimit>0 ? geometryLimit:std::max(1.0,refresh));
 const auto interval=std::chrono::nanoseconds(qint64(1000000000.0/target));
 if(motionTimer->interval()!=interval)motionTimer->setInterval(interval);
 if(!motionTimer->isActive())motionTimer->start();
}
void FramePacer::requestGeometry(){
 if(watchFrames() && frameSynchronized())return;
 if(geometrySocket->state()!=QLocalSocket::UnconnectedState || QDateTime::currentMSecsSinceEpoch()<nextGeometryAttempt)return;
 const auto runtime=qEnvironmentVariable("XDG_RUNTIME_DIR"),signature=qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE");if(runtime.isEmpty() || signature.isEmpty())return;
 geometryReply.clear();geometrySocket->connectToServer(runtime+"/hypr/"+signature+"/.socket.sock");geometryTimeout->start();
}
bool FramePacer::frameSynchronized()const{return lastFramePacket>0 && QDateTime::currentMSecsSinceEpoch()-lastFramePacket<1200;}
void FramePacer::consumeGeometry(const QByteArray& bytes,bool fromFrame){
 if(!fromFrame && frameSynchronized())return;
 const auto object=QJsonDocument::fromJson(bytes).object();
 const bool valid=object.value("supported").toBool() && object.value("windows").isObject();
 if(!valid && fromFrame)return;
 const auto now=QDateTime::currentMSecsSinceEpoch();
 const bool wasSynchronized=frameSynchronized();if(valid && fromFrame)lastFramePacket=now;
 nativeAnimating=valid && object.value("animating").toBool();if(valid)reportedRefresh=object.value("refreshHz").toDouble();updateGeometryTimer();
 // Drain old datagrams first, and honor an explicitly configured geometry cap.
 if(fromFrame && nativeAnimating && geometryLimit>0 && now-lastGeometryDelivery<1000.0/geometryLimit-.5)return;
 const auto next=valid ? object.value("windows").toObject().toVariantMap():QVariantMap{};
 if(hasGeometry!=valid || next!=renderedGeometry || wasSynchronized!=frameSynchronized()){
  hasGeometry=valid;renderedGeometry=next;lastGeometryDelivery=now;emit geometryChanged();
 }
 if(!valid)nextGeometryAttempt=now+2000;
}
bool FramePacer::watchFrames(){
 if(frameServer.isEmpty()){
  const auto runtime=qEnvironmentVariable("XDG_RUNTIME_DIR"),signature=qEnvironmentVariable("HYPRLAND_INSTANCE_SIGNATURE");
  if(runtime.isEmpty() || signature.isEmpty())return false;
  frameServer=(runtime+"/hypr/"+signature+"/quickintosh-frames.sock").toUtf8();
 }
 sockaddr_un server{};server.sun_family=AF_UNIX;if(frameServer.size()>=int(sizeof(server.sun_path)))return false;
 std::strcpy(server.sun_path,frameServer.constData());
 if(frameFd<0){
  framePath=(qEnvironmentVariable("XDG_RUNTIME_DIR")+"/qf-"+QString::number(getpid())+"-"+QUuid::createUuid().toString(QUuid::Id128).left(8)).toUtf8();
  sockaddr_un local{};local.sun_family=AF_UNIX;if(framePath.size()>=int(sizeof(local.sun_path)))return false;
  std::strcpy(local.sun_path,framePath.constData());frameFd=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);if(frameFd<0)return false;
  if(bind(frameFd,reinterpret_cast<sockaddr*>(&local),sizeof(local))){close(frameFd);frameFd=-1;return false;}
  chmod(framePath.constData(),0600);
  frameNotifier=new QSocketNotifier(frameFd,QSocketNotifier::Read,this);
  connect(frameNotifier,&QSocketNotifier::activated,this,[this,buffer=QByteArray(1024*1024,Qt::Uninitialized)]() mutable {
   ssize_t count,last=0;
   while((count=recv(frameFd,buffer.data(),buffer.size(),MSG_DONTWAIT))>0)last=count;
   if(last>0)consumeGeometry(QByteArray(buffer.constData(),last),true);
  });
 }
 return sendto(frameFd,"watch",5,MSG_DONTWAIT|MSG_NOSIGNAL,reinterpret_cast<sockaddr*>(&server),sizeof(server))==5;
}
void FramePacer::prepareWindows(bool keep){keepPrepared=keep;for(auto *w:windows.keys()){w->setPersistentGraphics(keep);w->setPersistentSceneGraph(keep);}}
void FramePacer::label(QObject *object,const QString &role){
 auto *window=qobject_cast<QQuickWindow *>(object);if(!window)return;attach(window);windows.value(window)->role=role;
}
QVariantList FramePacer::statistics(){
 QVariantList result;const auto now=Clock::now();
 for(auto i=windows.cbegin();i!=windows.cend();++i){
  const auto &s=i.value();std::lock_guard guard(s->mutex);
  std::vector<double> values(s->intervals.begin(),s->intervals.begin()+s->size);
  std::sort(values.begin(),values.end());double sum=0;for(double v:values)sum+=v;
  const bool active=s->lastFrame!=Clock::time_point{} && now-s->lastFrame<std::chrono::seconds(1);
  QVariantMap row{{"id",s->id},{"role",s->role},{"samples",int(s->size)},{"active",active},{"fps",active && sum>0 ? 1000.0*s->size/sum:0.0},
   {"p95Ms",values.empty() ? 0:values[size_t((values.size()-1)*.95)]},{"refreshHz",i.key()->screen() ? i.key()->screen()->refreshRate():0}};
  result.append(row);
 }
 return result;
}
