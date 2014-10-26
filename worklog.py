#! /usr/bin/python3

import argparse
from collections import Callable
from collections.abc import MutableSequence
from datetime import date, datetime, timedelta
import errno
import json
import re
import sys
import textwrap




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



class Task( object ):
    def __init__( self, start, description ):
        self.start = start
        self.description = description



class GoHome( Task ):
    def __init__( self, start, *unused ):
        super( GoHome, self ).__init__( start, 'go home' )



class Worklog( MutableSequence ):
    def __init__( self, when = None ):
        if when is None:
            self.when = date.today()
        else:
            self.when = date

        self.persist_path = os.path.expanduser( '~/.worklog/%s.json' % self.when.strftime( '%F' ) )

        try:
            with open( self.persist_path, 'r' ) as json_file:
                self.store = json.load( json_file, cls = KlassDecoder )
        except IOError as err:
            if err.errno == errno.ENOENT:
                self.store = list()
            else:
                raise

    def __getitem__( self, *args ):
        return self.store.__getitem__( *args )

    def __setitem__( self ):
        return self.store.__setitem__( *args )

    def __delitem__( self ):
        return self.store.__delitem__( *args )

    def __len__( self ):
        return self.store.__len__( *args )

    def insert( self ):
        return self.store.insert( *args )

    def save( self ):
        with open( self.persist_path, 'w' ) as json_file:
            json.dump( self.store, json_file, cls = KlassEncoder, indent = 4 )



class KlassEncoder( json.JSONEncoder ):
    """Encodes Task objects and datetime objects to JSON using __klass__ indicator key"""

    def default( self, obj ):
        if isinstance( obj, Task ):
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



class KlassDecoder( json.JSONDecoder ):
    """Decodes JSON representations that include the __klass__ indicator key

    The value for __klass__ must be a class defined in this scope and the rest
    of the dictionary must be keyword arguments to the constructor"""

    def __init__( self, *args, **kwargs ):
        kwargs['object_hook'] = self.dict_to_object
        super( KlassDecoder, self ).__init__( self, *args, **kwargs )

    def dict_to_object( self, d ):
        if '__klass__' not in d: return d

        klass = d.pop( '__klass__' )
        try:
            konstructor = globals()[klass]
        except KeyError:
            d['__klass__'] = klass
            return d
        else:
            return konstructor( **d )




def on_start( args ):
    sys.stdout.write( 'on_start\n{0!r}\n'.format( args ) )


def on_log( args ):
    sys.stdout.write( 'on_log\n{0!r}\n'.format( args ) )


def on_stop( args ):
    sys.stdout.write( 'on_stop\n{0!r}\n'.format( args ) )




def main():
    parser = argparse.ArgumentParser( description = 'manage and report time allocation',
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

            TIMEs
              Times should be provided in the form HH:MM. All times used, including "now",
              have their seconds zeroed out. All times provided on the command line are
              assumed to occur today.
        """ ),
    )
    sub_parser = parser.add_subparsers( dest = 'command' )

    common_parser = argparse.ArgumentParser( add_help = False )
    common_parser.add_argument( '--day', '-d', help = 'manage the worklog for DAY, defaults to today. should be provied in the format YYYY-MM-DD' )

    blurb = 'start a new task, closing the currently open task if any'
    start_parser = sub_parser.add_parser( 'start', help = blurb, description = blurb, parents = [ common_parser ] )
    start_parser.add_argument( '--ago', '-a', metavar = 'DURATION', help = 'start the task DURATION time ago, instead of now' )
    start_parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

    blurb = 'log a complete task'
    log_parser = sub_parser.add_parser( 'log', help = blurb, description = blurb, parents = [ common_parser ],
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = textwrap.dedent( """
            If an existing task is interrupted, it will be resumed as of the end of the
            newly logged task.
            
            You must provide exactly two of the three arguments""" ),
    )
    log_parser.add_argument( '--start', '-s', metavar = 'TIME', help = 'start the task at TIME' )
    log_parser.add_argument( '--end', '-e', metavar = 'TIME', help = 'end the task at TIME' )
    log_parser.add_argument( '--length', '-l', metavar = 'DURATION', help = 'calculate the missing start or end from the other using DURATION' )
    log_parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

    blurb = 'close the currently open task'
    stop_parser = sub_parser.add_parser( 'stop', help = blurb, description = blurb, parents = [ common_parser ] )
    stop_parser.add_argument( '--ago', '-a', metavar = 'DURATION', help = 'close the open task DURATION time ago, instead of now' )
    stop_parser.add_argument( 'description', metavar = 'DESCRIPTION', nargs = argparse.REMAINDER, help = "specify the task's description on the command line" )

    args = parser.parse_args()
    try:
        handler = globals()['on_%s' % args.command]
    except KeyError:
        parser.print_help()
    else:
        if isinstance( handler, Callable ):
            handler( args )
        else:
            parser.error( "unrecognized command: '%s'" % args.command )


if __name__ == '__main__':
    main()

