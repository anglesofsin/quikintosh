#!/usr/bin/env bash
# Explicit host setup only. Never run this on the developer's NixOS host.
set -euo pipefail
if [[ $EUID != 0 ]]; then echo 'Use sudo bash arch/system-setup.sh' >&2; exit 1; fi
source /etc/os-release
if [[ " ${ID:-} ${ID_LIKE:-} " != *' arch '* ]]; then echo 'Arch/Arch-derived system required' >&2; exit 1; fi
# Full upgrade: never create a pacman partial upgrade. Keep normal pacman prompts.
pacman -Syu --needed nix python dbus polkit gnome-keyring pipewire pipewire-pulse wireplumber \
  xdg-desktop-portal xdg-desktop-portal-gtk gvfs udisks2 fontconfig libnotify accountsservice upower bluez bluez-utils networkmanager ddcutil brightnessctl
systemctl enable --now nix-daemon.socket
python3 "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/pam_setup.py"
printf '%s\n' 'Host prerequisites installed. Run arch/install.sh doctor and install as your regular user.' \
  'Existing display manager, network configuration and GPU driver were not replaced.' \
  'If Nix denies access, follow the ArchWiki Nix build-users/daemon setup and open a new login shell.'
