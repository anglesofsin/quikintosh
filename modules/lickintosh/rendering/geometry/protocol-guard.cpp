// Compatibility guard for Hyprland 0.57's legacy toplevel exporter. Closing a
// window can race capture and leave the client's new frame ID unallocated.
#include "focus-restore-policy.hpp"
#include <hyprland/src/plugins/PluginAPI.hpp>
#include <hyprland/src/protocols/ToplevelExport.hpp>
#include <hyprland/src/protocols/ForeignToplevelWlr.hpp>
#include <hyprland/src/desktop/view/window/Window.hpp>
#include <hyprland/src/desktop/view/LayerSurface.hpp>
#include <hyprland/src/desktop/state/FocusState.hpp>
#include <hyprland/src/desktop/state/ViewState.hpp>
#include <hyprland/src/desktop/rule/windowRule/WindowRuleApplicator.hpp>
#include <hyprland/src/event/EventBus.hpp>
#include <hyprland/src/managers/input/InputManager.hpp>
#include <hyprland/src/protocols/LayerShell.hpp>
#include <algorithm>
#include <cxxabi.h>
#include <cstring>
#include <cstdlib>
#include <dlfcn.h>
#include <elf.h>
#include <fcntl.h>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string_view>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace {
// This is the actual std::function dispatch boundary. The host inlines
// captureToplevel into it, so hooking that exported member alone is ineffective.
using Capture = void (*)(const std::_Any_data&, CHyprlandToplevelExportManagerV1*&&,
                         uint32_t&&, int32_t&&, wl_resource*&&);
CFunctionHook* hook = nullptr;
CFunctionHook* restoreFocusHook = nullptr;
using RestoreFocus = bool (*)(CInputManager*, PHLMONITOR);
// Layer unmapping must never activate the last window on a hidden workspace.
// Explicit workspace/window dispatches continue through the normal focus path.
bool restoreVisibleFocus(CInputManager* input, PHLMONITOR monitor) {
    const auto window = Desktop::focusState()->window();
    if (shouldRefocusPointer(bool(monitor), !input->m_exclusiveKeyboardLSes.empty(), bool(window),
                            window && bool(window->m_workspace), window && window->m_workspace && window->m_workspace->visible())) {
        input->refocus();
        return true;
    }
    return reinterpret_cast<RestoreFocus>(restoreFocusHook->m_original)(input, monitor);
}
CHyprSignalListener focusListener;
std::vector<SP<CHyprlandToplevelExportFrameV1>> rejected;

void* captureBoundary() {
    const int fd = open("/proc/self/exe", O_RDONLY | O_CLOEXEC);
    struct stat st{};
    if (fd < 0) return nullptr;
    if (fstat(fd, &st) || st.st_size < static_cast<off_t>(sizeof(Elf64_Ehdr))) { close(fd); return nullptr; }
    const size_t length = st.st_size;
    const auto* data = static_cast<const unsigned char*>(mmap(nullptr, length, PROT_READ, MAP_PRIVATE, fd, 0));
    close(fd);
    if (data == MAP_FAILED) return nullptr;
    const auto cleanup = std::unique_ptr<const unsigned char, std::function<void(const unsigned char*)>>(
        data, [length](const auto* value) { munmap(const_cast<unsigned char*>(value), length); });
    const auto range = [length](uint64_t at, uint64_t size) { return at <= length && size <= length - at; };
    const auto* elf = reinterpret_cast<const Elf64_Ehdr*>(data);
    if (memcmp(elf->e_ident, ELFMAG, SELFMAG) || elf->e_ident[EI_CLASS] != ELFCLASS64 ||
        elf->e_shentsize != sizeof(Elf64_Shdr) || !range(elf->e_shoff, uint64_t(elf->e_shnum) * sizeof(Elf64_Shdr))) return nullptr;
    const auto* sections = reinterpret_cast<const Elf64_Shdr*>(data + elf->e_shoff);
    uintptr_t symbol = 0;
    for (size_t i = 0; i < elf->e_shnum; ++i) {
        const auto& table = sections[i];
        if (table.sh_type != SHT_SYMTAB || table.sh_entsize != sizeof(Elf64_Sym) ||
            table.sh_link >= elf->e_shnum || !range(table.sh_offset, table.sh_size)) continue;
        const auto& strings = sections[table.sh_link];
        if (!range(strings.sh_offset, strings.sh_size)) continue;
        const auto* entries = reinterpret_cast<const Elf64_Sym*>(data + table.sh_offset);
        for (size_t j = 0; j < table.sh_size / sizeof(Elf64_Sym); ++j) {
            const auto& item = entries[j];
            if (ELF64_ST_TYPE(item.st_info) != STT_FUNC || item.st_name >= strings.sh_size || !item.st_value) continue;
            const char* name = reinterpret_cast<const char*>(data + strings.sh_offset + item.st_name);
            const size_t available = strings.sh_size - item.st_name;
            const size_t count = strnlen(name, available);
            if (count == available) continue;
            const std::string_view mangled{name, count};
            if (!mangled.contains("CToplevelExportClient") || !mangled.contains("_M_invoke") || mangled.ends_with(".cold")) continue;
            int status = 0;
            const auto decoded = std::unique_ptr<char, decltype(&free)>(abi::__cxa_demangle(name, nullptr, nullptr, &status), &free);
            if (status || !decoded) continue;
            const std::string_view text{decoded.get()};
            if (!text.starts_with("std::_Function_handler<void (CHyprlandToplevelExportManagerV1*, unsigned int, int, wl_resource*)") ||
                !text.contains("CToplevelExportClient::CToplevelExportClient(") || !text.contains("::_M_invoke(")) continue;
            if (symbol) return nullptr;
            symbol = item.st_value;
        }
    }
    Dl_info executable{};
    if (!symbol || !dladdr(reinterpret_cast<void*>(&__hyprland_api_get_hash), &executable)) return nullptr;
    return reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(executable.dli_fbase) + symbol);
}
void retire(CHyprlandToplevelExportFrameV1* resource) {
    std::erase_if(rejected, [resource](const auto& entry) { return entry.get() == resource; });
}
void capture(const std::_Any_data& context, CHyprlandToplevelExportManagerV1*&& manager,
             uint32_t&& id, int32_t&& cursor, wl_resource*&& handle) {
    const auto window = PROTO::foreignToplevelWlr->windowFromHandleResource(handle);
    if (window) {
        reinterpret_cast<Capture>(hook->m_original)(context, std::move(manager), std::move(id), std::move(cursor), std::move(handle));
        return;
    }
    if (!manager || !manager->resource()) return;
    auto frame = makeShared<CHyprlandToplevelExportFrameV1>(manager->client(), manager->version(), id);
    if (!frame->resource()) { manager->noMemory(); return; }
    frame->setDestroy([](auto* value) { retire(value); });
    frame->setOnDestroy([](auto* value) { retire(value); });
    frame->setCopy([](auto*, wl_resource*, int32_t) {});
    rejected.push_back(frame);
    frame->sendFailed();
}
}
APICALL EXPORT std::string PLUGIN_API_VERSION() { return HYPRLAND_API_VERSION; }
APICALL EXPORT PLUGIN_DESCRIPTION_INFO PLUGIN_INIT(HANDLE handle) {
    if (std::string(__hyprland_api_get_hash()) != __hyprland_api_get_client_hash())
        throw std::runtime_error("Quickintosh capture guard: compositor ABI mismatch");
    auto* target = captureBoundary();
    if (!target) throw std::runtime_error("Quickintosh capture guard: exporter boundary not found");
    // Pending Wayland callbacks must stay valid across a manual plugin unload.
    Dl_info own{};
    if (!dladdr(reinterpret_cast<void*>(&capture), &own) || !dlopen(own.dli_fname, RTLD_NOW | RTLD_NODELETE))
        throw std::runtime_error("Quickintosh capture guard: callback lifetime unavailable");
    hook = HyprlandAPI::createFunctionHook(handle, target, reinterpret_cast<void*>(&capture));
    if (!hook || !hook->hook()) throw std::runtime_error("Quickintosh capture guard: hook failed");
    const auto restoreFunctions = HyprlandAPI::findFunctionsByName(handle, "refocusLastWindow");
    if (restoreFunctions.size() != 1) { hook->unhook(); throw std::runtime_error("Quickintosh focus guard: restore boundary unavailable"); }
    restoreFocusHook = HyprlandAPI::createFunctionHook(handle, restoreFunctions[0].address, reinterpret_cast<void*>(&restoreVisibleFocus));
    if (!restoreFocusHook || !restoreFocusHook->hook()) { hook->unhook(); throw std::runtime_error("Quickintosh focus guard: hook failed"); }
    focusListener = Event::bus()->m_events.window.open.listen([](PHLWINDOW window) {
        if (!window || window->m_ruleApplicator->noFocus().valueOrDefault() ||
            window->m_ruleApplicator->static_.noInitialFocus.value_or(false)) return;
        const auto layer = Desktop::viewState()->query().type(Desktop::View::VIEW_TYPE_LAYER_SURFACE)
            .surface(Desktop::focusState()->surface()).runLayer();
        // On-demand desktop keyboard ownership must not veto a new app's
        // initial focus. Explicit modal/exclusive keyboard ownership still wins.
        if (layer && layer->m_namespace == "quickshell:desktop" &&
            layer->m_layerSurface->m_current.keyboardInteractivity == ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_ON_DEMAND)
            window->m_state &= ~Desktop::View::WINDOW_STATE_NO_INITIAL_FOCUS;
    });
    return {"quickintosh-capture-guard", "Safe failed frames when captured windows close", "Quickintosh", "1.0.0"};
}
APICALL EXPORT void PLUGIN_EXIT() {
    focusListener.reset();
    if (restoreFocusHook) restoreFocusHook->unhook();
    restoreFocusHook = nullptr;
    if (hook) hook->unhook();
    hook = nullptr;
    // Failed resources remain inert until the owning client destroys them.
}
