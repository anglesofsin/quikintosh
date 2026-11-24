# Quickintosh: installation and development notes

For an Arch installation request, read `docs/ARCH.md`, `arch/README.md` and the installer before changing the host. The Arch method is pacman host prerequisites plus the pinned Nix bundle; do not run nixos-rebuild on Arch or invent a native AUR install path.

Run diagnosis first. Use the normal user's home, the isolated session/config and the installer's backups. Never run the user activation as root, overwrite the existing Hyprland config, replace a bootloader, force pacman conflicts, or silently stop a graphical session/call. Initial lock/unlock and logout/session switching need the user to be available.

Do not mix a distro Hyprland binary with the bundled plugin/config. Match the GPU wrapper to the actual driver. Preserve installer errors and inspect logs; do not skip failed steps and declare success. Read `docs/DISCORD.md` before adapting voice integration. Never copy credentials, Discord tokens or private user profiles into this repository.

Validation available without desktop interaction: `python3 tests/test_arch_installer.py`, router tests in `tests/nix-cli`, Python/shell syntax checks, and `nix build .#arch`. A successful build/temp-home test does not establish that PAM, graphics, portals and Discord work on a different Arch machine. State what was tested and keep the target-machine checklist explicit.
