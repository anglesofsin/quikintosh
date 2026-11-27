# Native material updates

Hyprglass 1.1 queues `preset()` and `layer()` declarations and commits them in
`config.reloaded`. A successful `hyprctl eval` does not commit those declarations.
A preferences file or `native-glass-runtime.json` entry is not evidence of a
rendered material. Global `hyprglass.config()` values have different live behavior.

Settings writes a canonical, typed `native-glass-config.lua` include under its
state directory. The managed Hyprland configuration loads that include after its
baseline plugin declarations. A changed include triggers a real configuration
reload, with rollback on a new config error. Reapplying identical values does not
reload. The existing Settings runtime lock serializes updates. Applications and
plugins stay running; no compositor replacement or plugin unload is involved.

Color opacity and corner updates do not change the material include. Corner
updates use only window rules/tags, never enqueue material declarations. The
menubar retains a minimal alpha footprint when blur is on and color opacity is
zero; an opaque color intentionally covers the material underneath.

Validate activation using compositor draw counters as well as UI/pixel checks.
With only the dock and menubar eligible, enabling the menubar must add one native
layer draw per displayed frame. Tests cover canonical/no-op updates, rollback,
profile serialization, corner isolation and transparent-color mask behavior.
