#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

PS1='[\u@\h \W]\$ '

## Load aliases
. $HOME/.aliases

# Update LS_COLORS
eval $(dircolors ~/.dircolors)

# WizardKit
export PYTHONPATH='/usr/local/bin'
