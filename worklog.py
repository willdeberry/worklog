#! /usr/bin/python3

import argparse
from collections import Callable
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta, time
import errno
from getpass import getpass
import itertools
from jira.client import JIRA
import json
import os
import re
import sys
import textwrap




class Abort( Exception ):
    pass


def now():
    """datetime.now() with seconds zeroed out"""
    now = datetime.now()
    return now.replace( second = 0, microsecond = 0 )


duration_factors = {
    'd': 60 * 60 * 8,
    'h': 60 * 60,
    'm': 60,
}

duration_re = re.compile( r'\s*(?:\s*(\d+(?:\.\d+)?)([{0}]))\s*'.format( ''.join( duration_factors.keys() ) ) )

def duration_to_timedelta( duration ):
    """Convert a human readable time duration to a timedelta object

    Recognizes a sequence of one or more integers or floats appended with a
    unit (d,h,m), optionally separated by whitespace.

    Fractions less than 1 require a leading 0.

    Examples:
        15m
        0.5h
        1.5h
        1d 4.5h
        1d 4h 30m
    """
    seconds = 0
    for match in duration_re.finditer( duration ):
        seconds = seconds + ( float( match.group(1) ) * duration_factors[match.group(2)] )
    return timedelta( seconds = seconds )



class Color( object ):

    ENABLED = True

    RESET = 0
    RESET_ENCODED = '\033[0m'

    BOLD_ON = 1
    BOLD_OFF = 22

    FAINT_ON = 2
    FAINT_OFF = 22

    ITALIC_ON = 3
    ITALIC_OFF = 23

    UNDERLINE_ON = 4
    UNDERLINE_OFF = 24

    INVERSE_ON = 7
    INVERSE_OFF = 27

    STRIKE_ON = 9
    STRIKE_OFF = 29

    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    PURPLE = 5
    CYAN = 6
    WHITE = 7
    DEFAULT = 9


    @staticmethod
    def encode( *values ):
        if not Color.ENABLED: return ''
        return '\033[{}m'.format( ';'.join( map( str, values ) ) )

    @staticmethod
    def build( before, value, after ):
        if not Color.ENABLED: return value
        return '{}{}{}'.format( Color.encode( *before ), value, Color.encode( *after ) )

    @staticmethod
    def vbuild( *values ):
        """infer the before and after based upon what's a string and what's a number; maybe a dangerous convenience"""
        before = list()
        value = None
        after = list()
        eat = lambda x: before.append( x )

        for v in values:
            if isinstance( v, int ):
                eat( v )
            if isinstance( v, str ):
                if value is None:
                    value = v
                    eat = lambda x: after.append( x )
                else:
                    raise ValueError( "too many strings in arguments" )

        return Color.build( before, value, after )


    @staticmethod
    def bold( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.BOLD_ON, str( s ), Color.BOLD_OFF )

    @staticmethod
    def faint( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.FAINT_ON, str( s ), Color.FAINT_OFF )

    @staticmethod
    def italic( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.ITALIC_ON, str( s ), Color.ITALIC_OFF )

    @staticmethod
    def underline( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.UNDERLINE_ON, str( s ), Color.UNDERLINE_OFF )

    @staticmethod
    def inverse( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.INVERSE_ON, str( s ), Color.INVERSE_OFF )

    @staticmethod
    def strike( s ):
        if not Color.ENABLED: return s
        return Color.vbuild( Color.STRIKE_ON, str( s ), Color.STRIKE_OFF )


    @staticmethod
    def colorize( value, fg = None, bg = None, intense = False, bold = False, faint = False, italic = False, underline = False, inverse = False, strike = False ):
        if not Color.ENABLED: return value
        if bold and faint: raise ValueError( 'bold and faint are mutually exclusive' )

        before = list()
        after = list()

        if intense:
            if fg is not None: fg += 60
            if bg is not None: bg += 60
        if fg is not None:
            fg += 30
            before.append( fg )
            after.append( Color.DEFAULT + 30 )
        if bg is not None:
            bg += 40
            before.append( bg )
            after.append( Color.DEFAULT + 40 )
        if bold:
            before.append( Color.BOLD_ON )
            after.append( Color.BOLD_OFF )
        if faint:
            before.append( Color.FAINT_ON )
            after.append( Color.FAINT_OFF )
        if italic:
            before.append( Color.ITALIC_ON )
            after.append( Color.ITALIC_OFF )
        if underline:
            before.append( Color.UNDERLINE_ON )
            after.append( Color.UNDERLINE_OFF )
        if inverse:
            before.append( Color.INVERSE_ON )
            after.append( Color.INVERSE_OFF )
        if strike:
            before.append( Color.STRIKE_ON )
            after.append( Color.STRIKE_OFF )

        return Color.build( before, value, after )


    @staticmethod
    def black( value, **kwargs ):
        kwargs['fg'] = Color.BLACK
        return Color.colorize( value, **kwargs )

    @staticmethod
    def red( value, **kwargs ):
        kwargs['fg'] = Color.RED
        return Color.colorize( value, **kwargs )

    @staticmethod
    def green( value, **kwargs ):
        kwargs['fg'] = Color.GREEN
        return Color.colorize( value, **kwargs )

    @staticmethod
    def yellow( value, **kwargs ):
        kwargs['fg'] = Color.YELLOW
        return Color.colorize( value, **kwargs )

    @staticmethod
    def blue( value, **kwargs ):
        kwargs['fg'] = Color.BLUE
        return Color.colorize( value, **kwargs )

    @staticmethod
    def magenta( value, **kwargs ):
        kwargs['fg'] = Color.MAGENTA
        return Color.colorize( value, **kwargs )

    @staticmethod
    def purple( value, **kwargs ):
        kwargs['fg'] = Color.PURPLE
        return Color.colorize( value, **kwargs )

    @staticmethod
    def cyan( value, **kwargs ):
        kwargs['fg'] = Color.CYAN
        return Color.colorize( value, **kwargs )

    @staticmethod
    def white( value, **kwargs ):
        kwargs['fg'] = Color.WHITE
        return Color.colorize( value, **kwargs )




SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 8

class Duration( object ):
    """Represents a time duration in just hours, and minutes.

    Easy for conversion to jira-format"""
    def __init__( self, delta ):
        self.delta = delta
        seconds = int( delta.total_seconds() )
        self.hours, seconds = divmod( seconds, SECONDS_IN_HOUR )
        self.minutes, seconds = divmod( seconds, SECONDS_IN_MINUTE )

    def __str__( self ):
        parts = list()
        if self.hours > 0: parts.append( '{:d}h'.format( self.hours ) )
        if self.minutes > 0: parts.append( '{:d}m'.format( self.minutes ) )
        return ' '.join( parts )

    def formatted( self ):
        parts = [ '', '' ]
        if self.hours > 0: parts[0] = '{:d}h'.format( self.hours )
        if self.minutes > 0: parts[1] = '{:d}m'.format( self.minutes )
        return '{:>3} {:>3}'.format( *parts )

    def colorized( self, **kwargs ):
        bold_kwargs = kwargs.copy()
        bold_kwargs['bold'] = True

        parts = [ '   ', '   ' ]
        if self.hours > 0:
            parts[0] = Color.cyan( '{:2d}'.format( self.hours ), **bold_kwargs ) + Color.cyan( 'h', **kwargs )
        if self.minutes > 0:
            parts[1] = Color.blue( '{:2d}'.format( self.minutes ), **bold_kwargs ) + Color.blue( 'm', **kwargs )
        return ' '.join( parts )



def resolve_at_or_ago( args, date ):
    if args.at:
        hour, minute = args.at.split( ':' )
        start = time( hour = int( hour ), minute = int( minute ) )
        return datetime.combine( date, start )
    elif args.ago:
        return now() - duration_to_timedelta( args.ago )
    else:
        return now()



class Task( object ):
    def __init__( self, start, ticket, description ):
        self.start = start
        self.ticket = ticket
        self.description = description.strip()

    def include_in_rollup( self ):
        if self.description.lower() == 'lunch':
            return False
        if self.description.lower() == 'break':
            return False
        return True



class GoHome( object ):
    def __init__( self, start, *unused ):
        self.start = start



class DummyRightNow( Task ):
    def __init__( self ):
        super( DummyRightNow, self ).__init__( start = now(), ticket = '', description = '' )



class Worklog( MutableSequence ):
    def __init__( self, when = None ):
        if when is None:
            self.when = date.today()
        elif isinstance( when, str ):
            self.when = datetime.strptime( when, '%Y-%m-%d' ).date()
        else:
            self.when = date

        self.persist_path = os.path.expanduser( '~/.worklog/{}-2.json'.format( self.when.strftime( '%F' ) ) )

        try:
            with open( self.persist_path, 'r' ) as json_file:
                self.store = json.load( json_file, object_hook = dict_to_object )
        except IOError as err:
            if err.errno == errno.ENOENT:
                self.store = list()
            else:
                raise

    def __getitem__( self, *args ):
        return self.store.__getitem__( *args )

    def __setitem__( self, *args ):
        return self.store.__setitem__( *args )

    def __delitem__( self, *args):
        return self.store.__delitem__( *args )

    def __len__( self, *args ):
        return self.store.__len__( *args )

    def insert( self, *args ):
        value = self.store.append( *args )
        self.store.sort( key = lambda t: t.start )
        return value

    def save( self ):
        directory = os.path.split( self.persist_path )[0]
        if not os.access( directory, os.F_OK ):
            os.makedirs( directory, mode=0o755 )
        with open( self.persist_path, 'w' ) as json_file:
            json.dump( self.store, json_file, cls = KlassEncoder, indent = 4 )

    def pairwise( self ):
        offset = self.store[1:]
        offset.append( DummyRightNow() )
        return zip( self.store, offset )



class KlassEncoder( json.JSONEncoder ):
    """Encodes Task objects and datetime objects to JSON using __klass__ indicator key"""

    def default( self, obj ):
        if isinstance( obj, ( Task, GoHome ) ):
            d = obj.__dict__.copy()
            d['__klass__'] = type( obj ).__name__
            return d
        elif isinstance( obj, datetime ):
            return {
                '__klass__' : 'datetime',
                'year' : obj.year,
                'month' : obj.month,
                'day' : obj.day,
                'hour' : obj.hour,
                'minute' : obj.minute,
                'second' : obj.second,
                'microsecond' : obj.microsecond,
            }
        else:
            return super( KlassEncoder, self ).default( obj )



# When this was an instance method on a subclass of json.JSONDecoder, python totally fucked up giving me
# TypeError: __init__() got multiple values for argument 'object_hook'
# even though I was overriding, not adding, my own object_hook
# pulling it out into a global function (ugh) and passing it along to json.load as the object_hook option
# worked around this stupid problem.
def dict_to_object( d ):
    if '__klass__' not in d: return d

    klass = d.pop( '__klass__' )
    try:
        konstructor = globals()[klass]
    except KeyError:
        d['__klass__'] = klass
        return d
    else:
        return konstructor( **d )




def parse_common_args( args ):
    return Worklog( when = args.day )


def on_start( args ):
    worklog = parse_common_args( args )

    start = resolve_at_or_ago( args, date = worklog.when )
    ticket = args.ticket

    try:
        description = ' '.join( args.description )
        while len( description.strip() ) == 0:
            try:
                description = input( 'Task description: ' )
            except KeyboardInterrupt:
                raise Abort()
            except EOFError:
                raise Abort()

        worklog.insert( Task( start = start, ticket = ticket, description = description ) )
        worklog.save()
    except Abort:
        sys.stdout.write( '\n' )

    report( worklog )


def on_resume( args ):
    worklog = parse_common_args( args )

    start = resolve_at_or_ago( args, date = worklog.when )

    try:
        descriptions = list()
        for description in reversed( [ task.description for task in worklog if isinstance( task, Task ) ] ):
            if description not in descriptions:
                descriptions.append( description )

        # when using resume, it means we're no longer working on the description that is now the first
        # item in this list, because of how we've sorted it. It is quite inconvenient for the first
        # choice to be the one we know for sure the user won't pick, bump it to the end of the line
        most_recent_description = descriptions.pop( 0 )
        descriptions.append( most_recent_description )

        for idx, description in enumerate( descriptions ):
            sys.stdout.write( '[{:d}] {}\n'.format( idx, description ) )

        description = None

        while description is None:
            try:
                idx = int( input( 'Which description: ' ) )
                description = descriptions[idx]
                for task in worklog:
                    if task.description == description:
                        ticket = task.ticket
            except KeyboardInterrupt:
                raise Abort()
            except EOFError:
                raise Abort()
            except ValueError:
                sys.stdout.write( 'Must be an integer between 0 and {:d}\n'.format( len( descriptions ) ) )
            except IndexError:
                sys.stdout.write( 'Must be an integer between 0 and {:d}\n'.format( len( descriptions ) ) )

        worklog.insert( Task( start = start, ticket = ticket, description = description ) )
        worklog.save()
    except Abort:
        sys.stdout.write( '\n' )

    report( worklog )


def on_stop( args ):
    worklog = parse_common_args( args )

    worklog.insert( GoHome( start = resolve_at_or_ago( args, date = worklog.when ) ) )
    worklog.save()
    report( worklog )


def log_to_jira( worklog ):
    options = { 'server': 'http://dev.jira.gwn' }
    username = input( '\nJira Username: ' )
    password = getpass()
    auth = ( username, password )
    jira = JIRA( options, basic_auth = auth )
    if len( worklog ) == 0:
        pass
    else:
        for task, next_task in worklog.pairwise():
            if isinstance( task, GoHome ): continue

            if task.ticket is not None:
                time = Duration( delta = next_task.start - task.start )
                started = '{}-{}-{}T{}:{}:00.000-0400'.format(
                    task.start.year,
                    task.start.month,
                    task.start.day,
                    task.start.hour,
                    task.start.minute
                )
                ticket = jira.issue( task.ticket )
                sys.stdout.write( 'Logging {} to ticket {}\n'.format( time, ticket ) )
                jira.add_worklog(
                    issue = ticket,
                    timeSpent = str( time ),
                    started = datetime.strptime( started, '%Y-%m-%dT%H:%M:%S.000%z' )
                )


def report( worklog ):
    total = timedelta( seconds = 0 )
    rollup = dict()

    sys.stdout.write( '{} {}\n'.format(
        Color.bold( 'Worklog Report for' ),
        Color.purple( worklog.when.strftime( '%F' ), bold = True )
    ) )

    if len( worklog ) == 0:
        sys.stdout.write( '    no entries\n' )
    else:
        for task, next_task in worklog.pairwise():
            if isinstance( task, GoHome ): continue

            if isinstance( next_task, DummyRightNow ):
                colorize_end_time = Color.yellow
            else:
                colorize_end_time = Color.green

            delta = next_task.start - task.start
            if task.include_in_rollup():
                total += delta
                if task.description not in rollup:
                    rollup[task.description] = delta
                else:
                    rollup[task.description] += delta

            sys.stdout.write( '    {:5s} {} {:5s} {}{!s:>7}{}  {}  {}\n'.format(
                Color.green( task.start.strftime( '%H:%M' ) ),
                Color.black( '-', intense = True ),
                colorize_end_time( next_task.start.strftime( '%H:%M' ) ),
                Color.black( '(', intense = True ),
                Duration( delta ).colorized(),
                Color.black( ')', intense = True ),
                task.ticket,
                task.description
            ) )

        sys.stdout.write( '\n    {!s:>7}  {}\n'.format(
            Duration( total ).colorized( underline = True ),
            Color.colorize( 'TOTAL', bold = True, underline = True )
        ) )
        for key in sorted( rollup.keys() ):
            sys.stdout.write( '    {!s:>7}  {}\n'.format(
                Duration( rollup[key] ).colorized(),
                Color.bold( key )
            ) )


def on_report( args ):
    worklog = parse_common_args( args )
    report( worklog )


def on_upload( args ):
    worklog = parse_common_args( args )
    log_to_jira( worklog )


def main():
    parser = argparse.ArgumentParser(
        description = 'manage and report time allocation',
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = textwrap.dedent( """
            DURATIONs
              Spans of time can be provided in a concise format, a series of integers or
              floats each appended with a unit: d, h, m. Whitespace between each component
              is optional. Fractions less than 1 require a leading 0.

              Note that a day is 8 hours.

              Examples:
                15m
                0.5h
                1.5h
                1d 4.5h
                1d 4h 30m
                1d4h30m

              Note that, while whitespace is optional, if you do specify a duration on the
              command line and it includes whitespace, you'll have to quote it.

            DATEs
              Dates should be provided in the form YYYY-MM-DD.

            TIMEs
              Times should be provided in the form HH:MM. All times used, including "now",
              have their seconds zeroed out. All times provided on the command line are
              assumed to occur today.
        """ ),
    )
    sub_parser = parser.add_subparsers( dest = 'command' )

    common_parser = argparse.ArgumentParser( add_help = False )
    common_parser.add_argument( '--day', '-d', help = 'manage the worklog for DATE, defaults to today' )

    blurb = 'start a new task, closing the currently open task if any'
    start_parser = sub_parser.add_parser( 'start', help = blurb, description = blurb, parents = [ common_parser ] )
    start_parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
    start_parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )
    start_parser.add_argument( '--ticket', metavar = 'TICKET', help = 'the TICKET associated with the task' )
    start_parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

    blurb = 'like start, but reuse the description from a previous task in this worklog by seleting it from a list'
    resume_parser = sub_parser.add_parser( 'resume', help = blurb, description = blurb, parents = [ common_parser ] )
    resume_parser.add_argument( '--ago', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
    resume_parser.add_argument( '--at', metavar = 'TIME', help = 'start the task at TIME, instead of now' )

    blurb = 'close the currently open task'
    stop_parser = sub_parser.add_parser( 'stop', help = blurb, description = blurb, parents = [ common_parser ] )
    stop_parser.add_argument( '--ago', metavar = 'DURATION', help = 'close the open task DURATION time ago, instead of now' )
    stop_parser.add_argument( '--at', metavar = 'TIME', help = 'close the open task at TIME, instead of now' )

    blurb = 'report the current state of the worklog'
    report_parser = sub_parser.add_parser( 'report', help = blurb, description = blurb, parents = [ common_parser ] )

    blurb = 'uploads worklog time to jira'
    upload_parser = sub_parser.add_parser( 'upload', help = blurb, description = blurb, parents = [ common_parser ] )

    args = parser.parse_args()
    try:
        handler = globals()['on_{}'.format( args.command )]
    except KeyError:
        parser.print_help()
    else:
        if isinstance( handler, Callable ):
            handler( args )
        else:
            parser.error( "unrecognized command: '{}'".format( args.command ) )


if __name__ == '__main__':
    try:
        main()
    except Abort:
        pass

