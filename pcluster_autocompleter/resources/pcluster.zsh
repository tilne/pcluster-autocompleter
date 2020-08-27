if [[ ! -o interactive ]]; then
    return
fi

compctl -K _pcluster pcluster

_pcluster() {
  local words completions
  read -cA words

  # TODO: figure out how to handle PATH, pyenv initialization
  if [ "${#words}" -eq 2 ]; then
    completions="$(pcluster_autocompleter)"
  else
    completions="$(pcluster_autocompleter ${words[2,-1]})"
  fi

  reply=(${(ps:\n:)completions})
}
