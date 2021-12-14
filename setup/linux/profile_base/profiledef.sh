#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="KIT_NAME_SHORT-Linux"
iso_label="KIT_NAME_SHORT_LINUX"
iso_publisher="SUPPORT_URL"
iso_application="KIT_NAME_FULL Linux Environment"
iso_version="$(date +%Y-%m-%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
file_permissions=(
  ["/etc/shadow"]="0:0:0400"
  ["/etc/gshadow"]="0:0:0400"
  ["/etc/skel/.ssh"]="0:0:0700"
  ["/etc/skel/.ssh/authorized_keys"]="0:0:0600"
  ["/etc/skel/.ssh/id_rsa"]="0:0:0600"
)
