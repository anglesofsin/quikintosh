# Floating application windows

On window.open, a new tiled window inherits floating from an existing floating
window with the same process id or a specific matching application class. This
also works when the source or destination is a special workspace. Generic
Electron and Quickshell classes do not match across unrelated processes.

Canvas windows and native portal choosers retain their dedicated policies.
Inheritance does not copy the source's geometry or persist an automatic layout
change as a user preference. Normal saved floating preferences still apply when
there is no live source window. The behavior applies to new windows and does not
convert all previously opened windows on reload.

Validation: floating_memory_test.lua and floating_inheritance_test.lua passed.
A private nested Hyprland instance opened a floating parent followed by a second
window with no floating rule; both reported floating=true via compositor IPC.
