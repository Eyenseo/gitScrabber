from argparse import ArgumentTypeError as err
import argparse
import os


class PathType(object):
    """ Taken from http://stackoverflow.com/a/33181083/1935553"""

    def __init__(self, exists=True, type='file', dash_ok=True):
        """
        :param  exists:   True: a path that does exist
                          False: a path that does not exist, in a valid parent
                          directory
                          None: don't care
        :param  type:     file, dir, symlink, None, or a function returning
                          True for valid paths
                          None: don't care
        :param  dash_ok:  whether to allow "-" as stdin/stdout
        """

        assert exists in (True, False, None)
        assert type in ('file', 'dir', 'symlink', None)\
            or hasattr(type, '__call__')

        self._exists = exists
        self._type = type
        self._dash_ok = dash_ok
        self.__name__ = type

    def __call__(self, string):
        if string == '-':
            # the special argument "-" means sys.std{in,out}
            if self._type == 'dir':
                raise err(
                    'standard input/output (-) not allowed as directory path')
            elif self._type == 'symlink':
                raise err(
                    'standard input/output (-) not allowed as symlink path')
            elif not self._dash_ok:
                raise err('standard input/output (-) not allowed')
        else:
            e = os.path.exists(string)
            if self._exists:
                if not e:
                    raise err("path does not exist: '%s'" % string)

                if self._type is None:
                    pass
                elif self._type == 'file':
                    if not os.path.isfile(string):
                        raise err("path is not a file: '%s'" % string)
                elif self._type == 'symlink':
                    if not os.path.symlink(string):
                        raise err("path is not a symlink: '%s'" % string)
                elif self._type == 'dir':
                    if not os.path.isdir(string):
                        raise err("path is not a directory: '%s'" % string)
                elif not self._type(string):
                    raise err("path not valid: '%s'" % string)
            else:
                if not self._exists and self._exists is not None and e:
                    raise err("path exists: '%s'" % string)

                p = os.path.dirname(os.path.normpath(string)) or '.'
                if not os.path.isdir(p):
                    raise err("parent path is not a directory: '%s'" % p)
                elif not os.path.exists(p):
                    raise err("parent directory does not exist: '%s'" % p)
        return string


def __setup_parser():
    """
    Set up  of the argument parser

    :returns: argument parser
    """
    parser = argparse.ArgumentParser(
        description='ScrabGitRepos',
        formatter_class=argparse.MetavarTypeHelpFormatter)
    parser.add_argument('-t', '--tasks',
                        type=PathType(exists=True, type='file'),
                        required=True,
                        help='Path to the tasks.yaml file')
    parser.add_argument('-g', '--gitdir',
                        type=PathType(exists=True, type='dir'),
                        default='.',
                        help='Directory where the repositories are cloned to')
    parser.add_argument('-r', '--report',
                        type=PathType(exists=True, type='file'),
                        default=None,
                        help='Path to an old report as base.')
    parser.add_argument('-s', '--savereport',
                        type=PathType(exists=None, type='file'),
                        default=None,
                        help='Path where the report will be saved to.')
    parser.add_argument('-p', '--printreport',
                        # type=bool,
                        action='store_true',
                        default=False,
                        help='If the report should be printed to stdout')
    parser.add_argument('-f', '--force',
                        # type=bool,
                        action='store_true',
                        default=False,
                        help='Forces the override of a present report')
    return parser


def __check_arguments(parser, args):
    """
    Check the given arguments for bade combinations

    :param  parser:  The parsed parser
    :param  args:    The arguments
    """
    if ('force' in vars(args) and
            'savereport' not in vars(args)):
        parser.error('Force is only needed to overwrite an existing report')

    if args.report == args.savereport and not args.force:
        parser.error('{} exists already! '
                     'Secify a new location for the new report or '
                     '--force override'.format(args.savereport))


def parse_args(args=None):
    """
    Parses the arguments

    :param    args:  The command line arguments

    :returns: The parsed arguments
    """
    parser = __setup_parser()
    args = None

    if(args):
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    __check_arguments(parser, parsed_args)

    return parsed_args
