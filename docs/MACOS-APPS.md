# macOS applications with Darling

Darling is a compatibility layer, not macOS or a virtual Mac. This integration
packages DarlingHQ's official **v0.1.20260608** Intel Linux release, verifies its
download hash and supplies its Linux libraries in a Nix FHS environment. Its
reported guest version is macOS 11.7.4; the Quickintosh desktop appearance does
not change that compatibility target to Tahoe. Modern Cocoa, Metal, DRM,
Apple Silicon-only software and Apple services may be unsupported. An app being
installed does not establish that it can run.

## Enable on NixOS

With the Quickintosh NixOS module enabled:

```nix
quickintosh.macApps.enable = true;
```

Or build the standalone package:

```sh
nix build .#darling
./result/bin/quickintosh-mac doctor
```

The user needs working subordinate UID/GID mappings (`/etc/subuid` and
`/etc/subgid`), `newuidmap`/`newgidmap` and unprivileged user namespaces. NixOS
normally creates these for normal users. Do not run the desktop launcher with
sudo. The runtime is x86_64 Linux only. Arch support for this optional runtime
requires those host prerequisites too; the main Arch installer does not enable
Darling automatically.

## Desktop workflow

Open **macOS Applications** from Spotlight or Launchpad. It offers installation,
opening installed apps, the Applications library in Finder,
a Darwin terminal and a runtime check. It uses the existing GTK theme.

- **`.app`:** choose the bundle folder. Quickintosh copies it into its separate
  library, preserves framework symlinks, reads its Info.plist and exports its
  icon and desktop launcher. It then appears alongside installed applications. The bundle executable is
  launched directly because this release’s LaunchServices `open` is a stub.
- **`.dmg`:** open with **macOS Installer**. The image is extracted read-only
  into temporary storage, then the chosen `.app` is installed into the library.
  This avoids the release's unreliable FUSE mounting in user namespaces; no
  root/loop-device mount is needed. Common UDIF/HFS images work through 7-Zip;
  encrypted or unusual images may not. Images containing a `.pkg` need that
  package extracted first. This is not the macOS disk-image Finder window.
- **`.pkg`:** the installer asks for confirmation, then runs Darwin's `installer`
  against the guest root. Package scripts are code: use trusted installers.
  Run `quickintosh-mac sync` after installing bundles manually in Darling.
- **Removal:** `quickintosh-mac remove '/path/to/Example.app'` moves managed apps
  to the Linux Trash and removes their generated launcher. It does not claim to
  reverse all scripts or dependencies installed by a `.pkg`.

The `.dmg`/Apple installer default associations apply through Quickintosh's
reversible desktop profile and are restored when leaving this rice. Other
desktop file associations are preserved. `.app` directories are not made the
default handler for all Linux folders.

```sh
quickintosh-mac install "$HOME/Downloads/Example.app"
quickintosh-mac install "$HOME/Downloads/Example.dmg" --app Example.app
quickintosh-mac list
quickintosh-mac open '/path/to/Example.app'
quickintosh-mac terminal
quickintosh-mac sync
```

## Storage and lifecycle

- Apps: `~/.local/share/quickintosh/mac-apps/Applications`
- Extracted bundle icons: `~/.local/share/quickintosh/mac-apps/icons`
- Darwin prefix: `~/.local/share/quickintosh/darling/prefix`
- Runtime log: `~/.local/state/quickintosh/darling.log`
- Launchers: `~/.local/share/applications/quickintosh-mac-*.desktop`

`DPREFIX` can select a different guest prefix. Standard Linux home directories
are accessible to Darwin through `/Volumes/SystemRoot`; this is **not a sandbox
for untrusted applications**. Darling's namespace privilege is not host root,
but applications can access your user files.

The namespace stays alive so subsequent launches reuse the same Darwin session.
Close macOS apps and run **`darling --stop`** to stop it. After a runtime update,
the launcher refuses to reuse an old runtime silently and asks for this step.
It does not terminate running apps automatically.

Troubleshoot with `quickintosh-mac doctor`, then inspect the runtime log and the
application's terminal output. The manager checks both initialization and guest
command completion so a failed installer is not reported as a success.

The Nix recipe also repairs the release's missing private-extern corecrypto
exports, publishing the existing function addresses required by Security/AppKit.
It does not substitute cryptographic implementations. A writable, versioned
Darwin base is prepared on first use; this initial copy can take a minute.

## Validation of this integration

On the development NixOS machine, the runtime executed Darwin `uname`,
`sw_vers`, successive commands in one session, quoted arguments and failing
guest commands. An AppKit/NSWindow test completed on a separate Xvfb display.
A fixture `.app` was copied, registered and launched through its bundle
executable. A real Rectangle disk image was extracted into a **private test
library**, including its Info.plist and ICNS-to-PNG icon; Rectangle itself was
not established as compatible. A generated `.pkg` fixture installed a text file
whose content was read back from `/Applications` inside Darwin.

The manager's tests (`python3 tests/test_mac_apps.py`) cover bundle validation,
Apple Silicon-only rejection, symlink preservation, duplicate protection,
desktop-entry escaping and removal/ejection path boundaries. None of these
tests implies universal third-party macOS application compatibility.

Upstream: [DarlingHQ](https://github.com/darlinghq/darling),
[official release](https://github.com/darlinghq/darling/releases/tag/v0.1.20260608),
[documentation](https://docs.darlinghq.org/).
