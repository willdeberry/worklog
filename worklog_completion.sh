
_comp_opts() {
	$1
}

_worklog() {
	local cur=${COMP_WORDS[COMP_CWORD]}
	local prev=${COMP_WORDS[COMP_CWORD-1]}
	case $prev in 
		start)
			COMPREPLY=($(compgen -W "--ago --at") -- $cur)
			return 0
			;;
		stop)
			COMPREPLY=($(compgen -W "--ago --at") -- $cur)
			return 0
			;;
		resume)
			COMPREPLY=($(compgen -W "--ago --at") -- $cur)
			;;
		report)
			return 0
			;;
	esac
	COMPREPLY=($(compgen -W "start stop resume report --day" -- $cur))
}

complete -F _worklog worklog
