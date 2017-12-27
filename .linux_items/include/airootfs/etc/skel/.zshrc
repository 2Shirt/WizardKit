# Oh My ZSH
export ZSH=$HOME/.oh-my-zsh
ZSH_THEME="lean"
DISABLE_AUTO_UPDATE="true"
HIST_STAMPS="yyyy-mm-dd"
plugins=(archlinux git sudo systemd tmux)
source $ZSH/oh-my-zsh.sh

# Wizard Kit
. $HOME/.aliases
eval $(dircolors ~/.dircolors)
