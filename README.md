# worklog

`worklog` is a simple command-line tool for tracking time. It presents a command line interface with which you simply
say "now I'm working on this" and later "now I'm working on that". At the end of the day, it can provide a summary
report telling you how long you worked on each task.

## installation

`worklog` is simple to install, just run `make install` with appropriate privileges:

```console
sudo make install
```

You can also uninstall it later:

```console
sudo make uninstall
```

By default it installs files under `/etc/bash_completion.d` and `/usr/local/bin`. To change these locations, you'll
need to provide alternatives on the command line:

```console
sudo make install prefix=/opt/ sysconfdir=/opt/etc/
```

The trailing `/` is critical. Remember to use the same override values when uninstalling

## usage

`worklog` has a few commands and each one accepts parameters.

### Common Options

These command line options are accepted by all of the commands

#### help

If you run `worklog` with `--help` and no command, you'll see the main usage and help.

```console
worklog --help
```

You can also run a command with `--help` to see usage and help for that particular command

```console
worklog start --help
```

#### day

By default, `worklog` operates on a log of today's work. You can invoke it with the `--day` option to cause it to
work with another day's log.

The argument should be in [ISO 8601](http://en.wikipedia.org/wiki/ISO_8601) format, YYYY-MM-DD.

```console
worklog report --day 2015-03-17
```

### start

Begin work and shift from one work description to a new one with the `start` command:

```console
worklog start
```

You will be prompted for a description of the work. You can also provide the description of the work on the command
line as the remaining arguments:

```console
worklog start fixing directory permissions when ~/.worklog is created
```

If you forget to log a change of focus right when it happens, worklog presents some options to specify when the entry
actually happened:

```console
worklog start --at 13:30 meeting about network design
```

```console
worklog start --ago 45m adjusting order of options with resume command
```

```console
worklog start --ago 1h30m adjusting order of options with resume command
```

Note that you can include whitespace in the `--ago` option, but on the command line it must be quoted:

```console
worklog start --ago '1h 30m' adjusting order of options with resume command
```

### resume

Shift your focus from one work task back to one you worked on earlier in the day with the `resume` command.

`resume` does not accept command line parameters for nor does it prompt for a work description. Instead, it uses all of
the task descriptions you've entered through `start` so far today to present to you a list of items to choose from.

```console
worklog resume
[0] adjusting order of options with resume command
[1] 13:30 meeting about network design
[2] lunch
[3] fixing directory permissions when ~/.worklog is created
Which description: 
```

Like `start`, `resume` accepts the `--at` and `--ago` options for adjusting the timing.

```console
worklog resume --ago 20m
```


### stop

End your day or a work session with the `stop` command.

```console
worklog stop
```

Like `start`, `resume` accepts the `--at` and `--ago` options for adjusting the timing.

```console
worklog stop --at 17:00
```

### report

`worklog` will give you a report of the day's work after each command is executed. So, after you switch gears with
`start`, you'll see the updated report after that change. After you end the day with `stop`, you'll see the day's
log.

Any other time you want to see the log, without making a change, you can use the `report` command.

```console
worklog report
```

The `report` command rolls up all task entries and adds up the time for each that have the same description.

#### Special Exceptions

`report` has some special rules for excluding entries in the rollup. If the task's full description is "lunch" or
"break", it remains in the log, but does not take part in the rollup.

Note that this feature is case-insensitive, but the *whole* description must be "lunch" or "break". The tool doesn't
want to assume that task descriptions like "figuring out why this break statement was removed" isn't real work. The
compromise is that entries like "lunch with Jim" are treated differently than "lunch".
