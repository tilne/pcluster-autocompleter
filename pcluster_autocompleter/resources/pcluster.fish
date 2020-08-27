function __fish_pcluster_needs_command
  set cmd (commandline -opc)
  if [ (count $cmd) -eq 1 -a $cmd[1] = 'pcluster' ]
    return 0
  end
  return 1
end

function __fish_pcluster_using_command
  set cmd (commandline -opc)
  if [ (count $cmd) -gt 1 ]
    if [ $argv[1] = $cmd[2] ]
      return 0
    end
  end
  return 1
end

complete -f -c pcluster -n '__fish_pcluster_needs_command' -a '(pcluster_autocompleter)'
for cmd in (pcluster_autocompleter)
  complete -f -c pcluster -n "__fish_pcluster_using_command $cmd" -a \
    "(pcluster_autocompleter (commandline -opc)[2..-1])"
end
