// Keep the client's geometry intact; extend only the shader's virtual rounding
// box past the lower display edge for Quickintosh's decorated maximize mode.
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/render/Context.hpp>
#include <hyprland/src/render/Shader.hpp>
#include <hyprland/src/desktop/view/window/Window.hpp>
#include <hyprland/src/desktop/rule/windowRule/WindowRuleApplicator.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <stdexcept>
namespace {
CFunctionHook *renderHook=nullptr,*uniformHook=nullptr;
thread_local float extension=0;
using Draw=WP<CShader> (*)(Render::GL::CHyprOpenGLImpl*,Render::CRenderContext&,SP<Render::ITexture>,const Render::GL::CHyprOpenGLImpl::STextureRenderData&,Render::eTextureType,const CBox&);
using Uniform=void (*)(CShader*,eShaderUniform,GLfloat,GLfloat);
WP<CShader> draw(Render::GL::CHyprOpenGLImpl* gl,Render::CRenderContext& ctx,SP<Render::ITexture> tex,const Render::GL::CHyprOpenGLImpl::STextureRenderData& data,Render::eTextureType type,const CBox& box){
 const float saved=extension;extension=0;
 const auto w=ctx.m_data.currentWindow.lock();const auto mon=ctx.m_data.pMonitor.lock();
 if(w && mon && mon->m_transform==WL_OUTPUT_TRANSFORM_NORMAL && data.round>0 && w->m_ruleApplicator->m_tagKeeper.isTagged("quickintosh-maximized") && Fullscreen::controller()->getFullscreenModes(w).internal==Fullscreen::FSMODE_MAXIMIZED)
  extension=data.round+2;
 auto result=reinterpret_cast<Draw>(renderHook->m_original)(gl,ctx,tex,data,type,box);extension=saved;return result;
}
void uniform(CShader* shader,eShaderUniform location,GLfloat x,GLfloat y){
 if(extension>0 && location==SHADER_FULL_SIZE)y+=extension;
 reinterpret_cast<Uniform>(uniformHook->m_original)(shader,location,x,y);
}
}
APICALL EXPORT std::string PLUGIN_API_VERSION(){return HYPRLAND_API_VERSION;}
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle){
 if(std::string(__hyprland_api_get_hash())!=__hyprland_api_get_client_hash())throw std::runtime_error("Maximize contour ABI mismatch");
 const auto draws=HyprlandAPI::findFunctionsByName(handle,"renderToFBInternal");const auto uniforms=HyprlandAPI::findFunctionsByName(handle,"setUniformFloat2");
 if(draws.size()!=1 || uniforms.size()!=1)throw std::runtime_error("Maximize contour boundaries unavailable");
 uniformHook=HyprlandAPI::createFunctionHook(handle,uniforms[0].address,reinterpret_cast<void*>(&uniform));
 renderHook=HyprlandAPI::createFunctionHook(handle,draws[0].address,reinterpret_cast<void*>(&draw));
 if(!uniformHook || !renderHook || !uniformHook->hook() || !renderHook->hook())throw std::runtime_error("Maximize contour hook failed");
 return {"quickintosh-maximize-contour","Square bottom corners in decorated maximize","Quickintosh","1.0.0"};
}
APICALL EXPORT void PLUGIN_EXIT(){if(renderHook)renderHook->unhook();if(uniformHook)uniformHook->unhook();}
