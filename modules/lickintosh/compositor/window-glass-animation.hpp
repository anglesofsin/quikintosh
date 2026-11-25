#pragma once

#include <array>
#include <optional>

#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/render/Context.hpp>

struct SResolveContext;
namespace GlassRenderer {
    struct SMaskInfo;
    struct SFrostInput;
}

namespace Quickintosh {
    using GlassImage = SP<Render::IFramebuffer>;
    using GlassViewport = std::optional<CBox>;
    using ApplyGlass = void (*)(Render::CRenderContext&, GlassImage, GlassImage, const CBox&,
        float, const std::array<float, 4>&, float, const Vector2D&, const SResolveContext&,
        const GlassRenderer::SMaskInfo*, float, const GlassRenderer::SFrostInput*, const GlassViewport&);
    using AnimateWindowGlass = bool (*)(PHLWINDOW, ApplyGlass, Render::CRenderContext&,
        const GlassImage&, const GlassImage&, const CBox&, float, const std::array<float, 4>&,
        float, const Vector2D&, const SResolveContext&, float, const GlassRenderer::SFrostInput*,
        const GlassViewport&);
    using SetWindowGlassAnimator = void (*)(HANDLE, AnimateWindowGlass);
    inline constexpr char WindowGlassAnimatorSymbol[] = "quickintoshSetWindowGlassAnimatorV1";
}
