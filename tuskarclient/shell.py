#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Command-line interface to the Tuskar API.
"""

from __future__ import print_function

import argparse
import logging
import logging.handlers
import sys

import six

import tuskarclient
from tuskarclient import client
import tuskarclient.common.utils as utils
from tuskarclient.openstack.common.apiclient import exceptions as exc

logger = logging.getLogger(__name__)


class TuskarShell(object):

    def __init__(self, raw_args,
                 argument_parser_class=argparse.ArgumentParser):
        self.raw_args = raw_args
        self.argument_parser_class = argument_parser_class

        self.partial_args = None
        self.parser = None
        self.subparsers = None
        self._prepare_parsers()

    def _prepare_parsers(self):
        nonversioned_parser = self._nonversioned_parser()
        self.partial_args = (
            nonversioned_parser.parse_known_args(self.raw_args)[0])
        self.parser, self.subparsers = (
            self._parser(self.partial_args.tuskar_api_version))

    def run(self):
        '''Run the CLI. Parse arguments and do the respective action.'''

        # run self.do_help() if we have no raw_args at all or just -h/--help
        if (not self.raw_args
                or self.raw_args in (['-h'], ['--help'])):
            self.do_help(self.partial_args)
            return 0

        args = self.parser.parse_args(self.raw_args)

        self._setup_logging(args.debug)

        # run self.do_help() if we have help subcommand or -h/--help option
        if args.func == self.do_help or args.help:
            self.do_help(args)
            return 0

        self._ensure_auth_info(args)

        tuskar_client = client.get_client(
            self.partial_args.tuskar_api_version, **args.__dict__)
        args.func(tuskar_client, args)

    def _ensure_auth_info(self, args):
        '''Ensure that authentication information is provided. Two variants
        of authentication are supported:
        - provide username, password, tenant and auth url
        - provide token and tuskar url (or auth url instead of tuskar url)
        '''
        if not args.os_auth_token:
            if not args.os_username:
                raise exc.CommandError("You must provide username via either "
                                       "--os-username or env[OS_USERNAME]")

            if not args.os_password:
                raise exc.CommandError("You must provide password via either "
                                       "--os-password or env[OS_PASSWORD]")

            if not args.os_tenant_id and not args.os_tenant_name:
                raise exc.CommandError("You must provide tenant via either "
                                       "--os-tenant-name or --os-tenant-id or "
                                       "env[OS_TENANT_NAME] or "
                                       "env[OS_TENANT_ID]")

            if not args.os_auth_url:
                raise exc.CommandError("You must provide auth URL via either "
                                       "--os-auth-url or env[OS_AUTH_URL]")
        else:
            if not args.tuskar_url and not args.os_auth_url:
                raise exc.CommandError("You must provide either "
                                       "--tuskar-url or --os-auth-url or "
                                       "env[TUSKAR_URL] or env[OS_AUTH_URL]")

    def _parser(self, version):
        '''Create a top level argument parser.

        :param version: version of Tuskar API (and corresponding CLI
            commands) to use
        :return: main parser and subparsers
        :rtype: (Parser, Subparsers)
        '''
        parser = self._nonversioned_parser()
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        versioned_shell = utils.import_versioned_module(version, 'shell')
        versioned_shell.enhance_parser(parser, subparsers)
        utils.define_commands_from_module(subparsers, self)
        return parser, subparsers

    def _nonversioned_parser(self):
        '''Create a basic parser that doesn't contain version-specific
        subcommands. This one is mainly useful for parsing which API
        version should be used for the versioned full blown parser and
        defining common version-agnostic options.
        '''
        parser = self.argument_parser_class(
            prog='tuskar',
            description='OpenStack Management CLI',
            add_help=False,
        )

        parser.add_argument('-h', '--help',
                            action='store_true',
                            help="Print this help message and exit.",
                            )

        parser.add_argument('--version',
                            action='version',
                            version=tuskarclient.__version__,
                            help="Shows the client version and exits.")

        parser.add_argument('-d', '--debug',
                            default=bool(utils.env('TUSKARCLIENT_DEBUG')),
                            action='store_true',
                            help='Defaults to env[TUSKARCLIENT_DEBUG].')

        parser.add_argument('--os-username',
                            default=utils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]',
                            )

        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--os-password',
                            default=utils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]',
                            )

        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--os-tenant-id',
                            default=utils.env('OS_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID]',
                            )

        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--os-tenant-name',
                            default=utils.env('OS_TENANT_NAME'),
                            help='Defaults to env[OS_TENANT_NAME]',
                            )

        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--os-auth-url',
                            default=utils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL]',
                            )

        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS,
                            )

        parser.add_argument('--os-auth-token',
                            default=utils.env('OS_AUTH_TOKEN',
                                              default=None),
                            help='Defaults to env[OS_AUTH_TOKEN]')

        parser.add_argument('--os_auth_token',
                            help=argparse.SUPPRESS)

        parser.add_argument('--tuskar-url',
                            default=utils.env('TUSKAR_URL'),
                            help='Defaults to env[TUSKAR_URL]')

        parser.add_argument('--tuskar_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--tuskar-api-version',
                            default=utils.env('TUSKAR_API_VERSION',
                                              default='2'),
                            help='Defaults to env[TUSKAR_API_VERSION] '
                            'or 2')

        parser.add_argument('--tuskar_api_version',
                            help=argparse.SUPPRESS)

        return parser

    @utils.arg(
        'command', metavar='<subcommand>', nargs='?',
        help='Display help for <subcommand>')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subparsers.choices:
                # print help for subcommand
                self.subparsers.choices[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            # print general help
            self.parser.print_help()

    def _setup_logging(self, debug):
        log_lvl = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(
            format="%(levelname)s (%(module)s) %(message)s",
            level=log_lvl)


def main():
    try:
        TuskarShell(sys.argv[1:]).run()
    except exc.CommandError as e:
        print(six.text_type(e), file=sys.stderr)
    except Exception as e:
        logger.exception("Exiting due to an error:")
        sys.exit(1)


if __name__ == '__main__':
    main()
