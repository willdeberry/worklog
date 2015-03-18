# worklog

`worklog` is a simple command-line tool for tracking time. It presents a command line interface with which you simply
say "now I'm working on this" and later "now I'm working on that". At the end of the day, it can provide a summary
report telling you how long you worked on each task.

## usage

`worklog` has a few commands and each one accepts parameters.

### Common Options

These command line options are accepted by all of the commands

#### help

If you run `worklog` with `--help` and no command, you'll see the main usage and help.

```bash session
worklog --help
```

You can also run a command with `--help` to see usage and help for that particular command

```bash session
worklog start --help
```

#### day

By default, `worklog` operates on a log of today's work. You can invoke it with the `--day` option to cause it to
work with another day's log.

The argument should be in [ISO 8601](http://en.wikipedia.org/wiki/ISO_8601) format, YYYY-MM-DD.

```bash session
worklog report --day 2015-03-17
```

### start

Begin work and shift from one work description to a new one with the `start` command:

```bash session
worklog start
```

You will be prompted for a description of the work. You can also provide the description of the work on the command
line as the remaining arguments:

```bash session
worklog start fixing directory permissions when ~/.worklog is created
```

If you forget to log a change of focus right when it happens, worklog presents some options to specify when the entry
actually happened:

```bash session
workl start --at 13:30 meeting about network design
```

```bash session
worklog start --ago 45m adjusting order of options with resume command
```

```bash session
worklog start --ago 1h30m adjusting order of options with resume command
```

Note that you can include whitespace in the `--ago` option, but on the command line it must be quoted:

```bash session
worklog start --ago '1h 30m' adjusting order of options with resume command
```

### resume

Shift your focus from one work task back to one you worked on earlier in the day with the `resume` command.

`resume` does not accept command line parameters for nor does it prompt for a work description. Instead, it uses all of
the task descriptions you've entered through `start` so far today to present to you a list of items to choose from.

```bash session
worklog resume
[0] adjusting order of options with resume command
[1] 13:30 meeting about network design
[2] lunch
[3] fixing directory permissions when ~/.worklog is created
Which description: 
```

Like `start`, `resume` accepts the `--at` and `--ago` options for adjusting the timing.

```bash session
worklog resume --ago 20m
```


### stop

End your day or a work session with the `stop` command.

```bash session
worklog stop
```

Like `start`, `resume` accepts the `--at` and `--ago` options for adjusting the timing.

```bash session
worklog stop --at 17:00
```

### report

`worklog` will give you a report of the day's work after each command is executed. So, after you switch gears with
`start`, you'll see the updated report after that change. After you end the day with `stop`, you'll see the day's
log.

Any other time you want to see the log, without making a change, you can use the `report` command.

```bash session
worklog report
```

