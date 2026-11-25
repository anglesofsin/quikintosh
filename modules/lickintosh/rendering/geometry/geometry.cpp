// Read-only animation telemetry and frame notifications; no render mutation or dispatchers.
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/debug/HyprCtl.hpp>
#include <format>
#include <algorithm>
#include <stdexcept>
#include <chrono>
#include <vector>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstring>
#include <cerrno>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <wayland-server-core.h>
#if __has_include(<hyprland/src/desktop/view/Window.hpp>)
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/desktop/Workspace.hpp>
#include <hyprland/src/output/Monitor.hpp>
#define QUICKINTOSH_CURRENT_GEOMETRY 1
#endif
static HANDLE handle;
static SP<SHyprCtlCommand> command;
APICALL EXPORT std::string PLUGIN_API_VERSION(){return HYPRLAND_API_VERSION;}
static std::string snapshot(eHyprCtlOutputFormat,std::string){
#ifndef QUICKINTOSH_CURRENT_GEOMETRY
 return R"({"supported":false,"windows":{}})";
#else
 std::string result=R"({"supported":true,"windows":{)";bool comma=false,animating=false;double refresh=0;
 for(const auto &w:Desktop::windowState()->windows()){
  if(!w || !w->m_isMapped || w->isHidden() || !w->m_workspace)continue;
  const auto ws=w->m_workspace;const auto mon=ws->m_monitor.lock();if(!mon)continue;
  const bool pinned=w->m_pinned;
  const auto offset=pinned ? Vector2D{}:ws->m_renderOffset->value();
  const bool visible=pinned || ws->m_visible || ws->m_renderOffset->isBeingAnimated() || ws->m_alpha->isBeingAnimated();
  const double alpha=(pinned ? 1:ws->m_alpha->value())*w->alphaValue(Desktop::View::WINDOW_ALPHA_FADE);
  animating=animating || ws->m_renderOffset->isBeingAnimated() || ws->m_alpha->isBeingAnimated();refresh=std::max(refresh,double(mon->m_refreshRate));
  if(!visible || alpha<=.001)continue;
  const auto at=w->position(Desktop::View::IGeometric::GEOMETRIC_CURRENT)+offset+w->m_floatingOffset;
  const auto size=w->size(Desktop::View::IGeometric::GEOMETRIC_CURRENT);
  if(comma)result+=',';comma=true;
  result+=std::format(R"("{:x}":{{"at":[{:.3f},{:.3f}],"size":[{:.3f},{:.3f}],"visible":{},"opacity":{:.4f},"clipActive":{},"clip":[{:.3f},{:.3f},{:.3f},{:.3f}]}})",
   reinterpret_cast<uintptr_t>(w.get()),at.x,at.y,size.x,size.y,(visible && alpha>.001 ? "true":"false"),alpha,(!pinned && ws->m_renderOffset->isBeingAnimated() ? "true":"false"),
   mon->m_position.x+offset.x,mon->m_position.y+offset.y,mon->m_size.x,mon->m_size.y);
 }
 result+=std::format(R"(}},"animating":{},"refreshHz":{:.3f}}})",animating ? "true":"false",refresh);return result;
#endif
}
// Frame notifications run after AnimationManager::frameTick, never modify rendering.
static int frameFd=-1;
static wl_event_source* frameSource=nullptr;
static CHyprSignalListener frameListener;
static std::string framePath;
using Steady=std::chrono::steady_clock;
struct Subscriber{sockaddr_un address;socklen_t length;Steady::time_point expires;};
static std::vector<Subscriber> subscribers;
static void publishFrame(){
 const auto now=Steady::now();
 std::erase_if(subscribers,[&](const auto& s){return s.expires<now;});
 if(subscribers.empty())return;
 const auto data=snapshot(eHyprCtlOutputFormat{},"");
 std::erase_if(subscribers,[&](const auto& s){
  const auto n=sendto(frameFd,data.data(),data.size(),MSG_DONTWAIT|MSG_NOSIGNAL,reinterpret_cast<const sockaddr*>(&s.address),s.length);
  return n<0 && (errno==ENOENT || errno==ECONNREFUSED);
 });
}
static int readSubscriptions(int,uint32_t,void*){
 char message[16];sockaddr_un peer{};socklen_t length=sizeof(peer);
 while(true){
  length=sizeof(peer);const auto n=recvfrom(frameFd,message,sizeof(message),MSG_DONTWAIT,reinterpret_cast<sockaddr*>(&peer),&length);
  if(n<0)break;
  peer.sun_path[sizeof(peer.sun_path)-1]=0;
  if(n!=5 || std::memcmp(message,"watch",5)!=0 || peer.sun_family!=AF_UNIX || !peer.sun_path[0])continue;
  // Subscriber sockets must be owned by this session's user.
  struct stat info{};if(lstat(peer.sun_path,&info) || info.st_uid!=getuid() || !S_ISSOCK(info.st_mode))continue;
  bool found=false;for(auto& sub:subscribers)if(std::strcmp(sub.address.sun_path,peer.sun_path)==0){sub.expires=Steady::now()+std::chrono::seconds(2);found=true;break;}
  if(!found && subscribers.size()<32)subscribers.push_back({peer,length,Steady::now()+std::chrono::seconds(2)});
 }
 publishFrame();return 0;
}
static void stopFrames(){
 frameListener.reset();if(frameSource){wl_event_source_remove(frameSource);frameSource=nullptr;}
 if(frameFd>=0){close(frameFd);frameFd=-1;}if(!framePath.empty())unlink(framePath.c_str());subscribers.clear();
}
static void startFrames(){
 const char* runtime=getenv("XDG_RUNTIME_DIR");const char* signature=getenv("HYPRLAND_INSTANCE_SIGNATURE");
 if(!runtime || !signature)return;
 framePath=std::string(runtime)+"/hypr/"+signature+"/quickintosh-frames.sock";
 sockaddr_un address{};address.sun_family=AF_UNIX;if(framePath.size()>=sizeof(address.sun_path))return;
 std::strcpy(address.sun_path,framePath.c_str());frameFd=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);if(frameFd<0)return;
 unlink(framePath.c_str());if(bind(frameFd,reinterpret_cast<sockaddr*>(&address),sizeof(address))){stopFrames();return;}
 chmod(framePath.c_str(),0600);
 frameSource=wl_event_loop_add_fd(g_pCompositor->m_wlEventLoop,frameFd,WL_EVENT_READABLE,readSubscriptions,nullptr);
 if(!frameSource){stopFrames();return;}
 frameListener=Event::bus()->m_events.render.pre.listen([](PHLMONITOR){publishFrame();});
}
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE value){
 if(std::string(__hyprland_api_get_hash())!=std::string(__hyprland_api_get_client_hash()))throw std::runtime_error("Quickintosh geometry: compositor ABI mismatch");
 handle=value;command=HyprlandAPI::registerHyprCtlCommand(handle,{"quickintosh:geometry",true,snapshot});
 if(!command)throw std::runtime_error("Quickintosh geometry: IPC registration failed");
 startFrames();
 return {"quickintosh-geometry","Read-only rendered window/workspace geometry","Quickintosh","1.1.0"};
}
APICALL EXPORT void PLUGIN_EXIT(){stopFrames();if(command)HyprlandAPI::unregisterHyprCtlCommand(handle,command);command.reset();}
