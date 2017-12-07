#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

PS1='[\u@\h \W]\$ '

## Load aliases
. $HOME/.aliases

## Start ssh agent
eval $(/usr/bin/ssh-agent)

