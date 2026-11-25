// Read-only animation telemetry: no render hooks, dispatchers, or window changes.
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/debug/HyprCtl.hpp>
#include <format>
#include <algorithm>
#include <stdexcept>
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
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE value){
 if(std::string(__hyprland_api_get_hash())!=std::string(__hyprland_api_get_client_hash()))throw std::runtime_error("Quickintosh geometry: compositor ABI mismatch");
 handle=value;command=HyprlandAPI::registerHyprCtlCommand(handle,{"quickintosh:geometry",true,snapshot});
 if(!command)throw std::runtime_error("Quickintosh geometry: IPC registration failed");
 return {"quickintosh-geometry","Read-only rendered window/workspace geometry","Quickintosh","1.0.0"};
}
APICALL EXPORT void PLUGIN_EXIT(){if(command)HyprlandAPI::unregisterHyprCtlCommand(handle,command);command.reset();}
