.SHELL: /bin/sh 

.PHONY: install

prefix ?= /usr/local/
bindir = $(prefix)bin/
sysconfdir = /etc/

PWD ?= $(shell pwd)

BASHCOMPDIR ?= $(sysconfdir)bash_completion.d/
BASHCOMP ?= $(PWD)/worklog_completion.sh
SCRIPT ?= $(PWD)/worklog.py

install: $(BASHCOMPDIR)worklog_completion.sh $(bindir)worklog

$(BASHCOMPDIR)worklog_completion.sh: $(BASHCOMPDIR)
	ln -s $(BASHCOMP) $@

$(bindir)worklog:
	ln -s $(SCRIPT) $@
