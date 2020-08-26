_pcluster() {
  COMPREPLY=()
  local word="${COMP_WORDS[COMP_CWORD]}"

  echo >> /tmp/pcluster-completions-log.txt COMP_WORDS: ${COMP_WORDS}
  echo >> /tmp/pcluster-completions-log.txt COMP_CWORD: ${COMP_CWORD}
  echo >> /tmp/pcluster-completions-log.txt word:       ${word}
  if [ "$COMP_CWORD" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$(get_pcluster_completion_candidates.py)" -- "$word") )
  else
    local words=("${COMP_WORDS[@]}")
    unset words[0]
    unset words[$COMP_CWORD]
    local completions=$(get_pcluster_completion_candidates.py "${words[@]}")
    COMPREPLY=( $(compgen -W "$completions" -- "$word") )
  fi
}

complete -F _pcluster pcluster
