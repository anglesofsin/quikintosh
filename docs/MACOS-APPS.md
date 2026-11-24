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
- **`.dmg`:** open with **macOS Installer**. The installer uses
  [darling-dmg](https://github.com/darlinghq/darling-dmg) to mount HFS+/HFSX
  images read-only on the Linux host, then copies the chosen `.app` into the
  library and unmounts the image. It does not mount inside Darling's user
  namespace or require root/loop devices. A working host `/dev/fuse` and
  `fusermount` helper are needed. If mounting is unavailable or the image uses
  an unsupported filesystem, 7-Zip extraction remains the fallback; encrypted
  or unusual images may not work. A busy mount is retained rather than
  recursively deleted. Images containing a `.pkg` need that
  package extracted first. This is not the macOS disk-image Finder window.
- **`.pkg`:** the installer asks for confirmation, then runs Darwin's `installer`
  against the guest root. Package scripts are code: use trusted installers.
  Run `quickintosh-mac sync` after installing bundles manually in Darling.
- **Removal:** `quickintosh-mac remove '/path/to/Example.app'` moves managed apps
  to the Linux Trash and removes their generated launcher. It does not claim to
  reverse all scripts or dependencies installed by a `.pkg`.

The `.dmg`/Apple installer default associations apply through Quickintosh's
reversible desktop profile and are restored when leaving this rice. Other
desktop file associations are preserved. Linux may classify `.pkg` as XAR, so
Quickintosh also associates XAR with the installer while this rice is active;
the manager refuses unrelated non-`.pkg` XAR archives. `.app` directories are not made the
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

`darling-dmg` is also installed as a standalone command for manual read-only
mounts: `darling-dmg '/path/Example.dmg' '/existing/empty/mountpoint' -o ro`.
Unmount with the host `fusermount -u '/existing/empty/mountpoint'` before
removing the mount directory. The package is pinned through this repository's
Nixpkgs lock, including its upstream revision and source hash.

### Arc Browser compatibility

Arc **1.174.2 (91442)** was tested with this integration. Its HFS+ image mounts
successfully with `darling-dmg`, and the installed bundle includes both Intel
and ARM executables. Launching its Intel executable on the packaged Darling
release aborts at `Combine.framework: image not found`. Its Info.plist requires
macOS 13. Installing the disk-image reader does not provide missing macOS
frameworks or make this Arc release runnable. The original DMG and installed
bundle are preserved; no fake framework or version spoof is used.

## Separate development runtime

An optional **development runtime**, not a supported Arc runtime, overlays the
official Darling release with Swift libraries, the OpenCombine-based Combine
build and the swift-crypto-based CryptoKit build published by VibeDarling, plus
a source-built GameplayKit subset. It is not a full build of VibeDarling. Payload
revision `78a04e469481027bf4294022a4bffc71a41886d0` and each LFS object's SHA-256
are recorded in `packages/darling-swift-payload.json`; no application binaries
or Apple operating-system frameworks are committed to this repository.

```sh
nix build .#darling-experimental -o result-darling-experimental
./result-darling-experimental/bin/darling-experimental shell /usr/bin/uname -s
```

To add the command to the optional NixOS macOS-app integration:

```nix
quickintosh.macApps.enable = true;
quickintosh.macApps.experimental.enable = true;
```

Then select it explicitly:

```sh
quickintosh-mac --runtime experimental doctor
quickintosh-mac --runtime experimental open '/path/to/Example.app'
darling-experimental --stop
```

The default `darling` command and app launchers keep using the stable runtime.
The experimental command uses
`~/.local/share/quickintosh/darling-experimental/prefix`; it does not reuse or
upgrade the stable prefix. An explicit `DPREFIX` overrides either default, so
do not point both commands at the same active prefix. Applications are still
host-user programs, not a security sandbox.

The package builds a small `libswiftCoreCompat` containing forwarding aliases
and force-load markers, and supplies the Swift library search path **inside
guest shells only**. It intentionally omits the upstream compatibility file's
UI/metadata placeholders that return zero rather than implementing an API.
Component licenses and the payload manifest ship under
`share/doc/darling-experimental`.

In the private test environment, Darwin commands ran and Python's `ctypes`
loaded the real Combine framework after resolving its auxiliary-library and
Swift search-path dependencies. This is a loader test, not proof of complete
Combine behavior. Arc progressed past missing Combine, CryptoKit and GameplayKit
to missing NaturalLanguage; no Arc browser window was established. Intel import
analysis of the Arc 1.174.2 main executable found 33 CryptoKit and 1,615 SwiftUI
references. Those are
imported-reference counts, not counts of implemented features. The pinned
CryptoKit executable was verified to include Intel and ARM slices,
despite the upstream installer still restricting it to ARM. The integration
installs that real executable rather than substituting cryptographic operations.
Generic stubs would not implement the remaining Swift types, language analysis
or user-interface behavior it needs.

The authored GameplayKit subset supplies `GKRandomSource` and
`GKMersenneTwisterRandomSource`: deterministic MT19937-64 state, seeding, state
copy, bounded integers with rejection sampling, floating-point/Boolean draws and
Fisher–Yates shuffling. The engine follows Apple's public description of
`std::mt19937_64` compatibility. The choice of low 32 bits for `nextInt` and high
24 bits for `nextUniform` is a range-correct mapping; exact parity of those
projections with Apple's implementation was not measured. Encoding/decoding and
the rest of GameplayKit are not supplied. The fallback `GKRandomSource` uses the
hosted Darwin `arc4random_buf`, not a constant result.

`tests/test_gameplaykit.py` compares 50,000 outputs with the independent C++
standard-library engine. Its optional Darwin test creates and shuts down a
separate temporary prefix, loads Combine/CryptoKit/GameplayKit and exercises seed
replay, state copies, bounds, floats, Booleans and non-mutating shuffling:

```sh
QUICKINTOSH_TEST_CXX=/path/to/c++ \
QUICKINTOSH_TEST_DARLING=/path/to/darling-experimental \
python3 tests/test_gameplaykit.py
```

These tests do not claim that the full Arc application starts or renders pages.
The launcher also checks loader diagnostics during its startup grace period,
even if the Darling transport returns zero or is still exiting. Log reads are
bounded; stable and experimental launch logs use separate filenames.

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
