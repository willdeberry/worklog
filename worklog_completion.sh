
_worklog(){
	local options

	case "${COMP_WORDS[1]}" in
		start|stop|resume)
			options="--ago --at --day"
			;;
		report)
			options="--day"
			;;
		*)
			options="start stop resume report"
			;;
	esac

	COMPREPLY=( $( compgen -W "${options}" -- "${COMP_WORDS[COMP_CWORD]}" ) )
}

complete -F _worklog worklog

