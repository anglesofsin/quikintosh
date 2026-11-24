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
install -d -m755 /etc/pam.d
for service in lickintosh-lock lickintosh-lock-fprint; do
  if [[ ! -e /etc/pam.d/$service ]]; then
    install -m644 /dev/stdin "/etc/pam.d/$service" <<'PAM'
# Quickintosh on Arch. Authentication is delegated to the host system's policy.
auth include system-auth
account include system-auth
password include system-auth
session include system-auth
PAM
  fi
done
printf '%s\n' 'Host prerequisites installed. Run arch/install.sh doctor and install as your regular user.' \
  'Existing display manager, network configuration and GPU driver were not replaced.' \
  'If Nix denies access, follow the ArchWiki Nix build-users/daemon setup and open a new login shell.'
