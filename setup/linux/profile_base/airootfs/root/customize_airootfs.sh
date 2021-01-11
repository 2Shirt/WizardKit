#!/bin/env bash
#
# Warning: customize_airootfs.sh is deprecated! Support for it will be removed in a future archiso version.

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail


sed -i 's/#\(en_US\.UTF-8\)/\1/' /etc/locale.gen
locale-gen

# Sudo
echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# SSH
#rm /root/.ssh/id*
#rm /root/.zlogin
