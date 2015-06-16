#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

from __future__ import print_function

import logging
import os
import shutil
import sys

from cliff import command
from cliff import lister
from cliff import show

from tuskarclient.common import formatting
from tuskarclient.common import utils
from tuskarclient.openstack.common.apiclient import exceptions as exc


class CreateManagementPlan(show.ShowOne):
    """Create a Management Plan."""

    log = logging.getLogger(__name__ + '.CreateManagementPlan')

    def get_parser(self, prog_name):
        parser = super(CreateManagementPlan, self).get_parser(prog_name)

        parser.add_argument(
            'name',
            help="Name of the plan being created."
        )

        parser.add_argument(
            '-d', '--description',
            help='A textual description of the plan.')

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management
        name = parsed_args.name

        try:
            plan = client.plans.create(
                name=name,
                description=parsed_args.description
            )
        except exc.Conflict:
            raise exc.CommandError(
                'Plan with name "%s" already exists.' % name)

        return self.dict2columns(plan.to_dict())


class DeleteManagementPlan(command.Command):
    """Delete a Management Plan."""

    log = logging.getLogger(__name__ + '.DeleteManagementPlan')

    def get_parser(self, prog_name):
        parser = super(DeleteManagementPlan, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan being deleted."
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        client.plans.delete(parsed_args.plan_uuid)


class ListManagementPlans(lister.Lister):
    """List the Management Plans."""

    log = logging.getLogger(__name__ + '.ListManagementPlans')

    def get_parser(self, prog_name):
        parser = super(ListManagementPlans, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        plans = client.plans.list()

        return (
            ('uuid', 'name', 'description', 'roles'),
            ((p.uuid, p.name, p.description,
                ', '.join(r.name for r in p.roles))
                for p in plans)
        )


class SetManagementPlan(show.ShowOne):
    """Update a Management Plans properties."""

    log = logging.getLogger(__name__ + '.SetManagementPlan')

    def get_parser(self, prog_name):
        parser = super(SetManagementPlan, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan being updated."
        )

        parser.add_argument(
            '-P', '--parameter', dest='parameters', metavar='<KEY1=VALUE1>',
            help=('Set a parameter in the Plan. This can be specified '
                  'multiple times.'),
            action='append'
        )

        parser.add_argument(
            '-F', '--flavor', dest='flavors', metavar='<ROLE=FLAVOR>',
            help=('Set the flavor for a role in the Plan. This can be '
                  'specified multiple times.'),
            action='append'
        )

        parser.add_argument(
            '-S', '--scale', dest='scales', metavar='<ROLE=SCALE-COUNT>',
            help=('Set the Scale count for a role in the Plan. This can be '
                  'specified multiple times.'),
            action='append'
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        plan = client.plans.get(parsed_args.plan_uuid)
        roles = plan.roles

        patch = []

        patch.extend(utils.parameters_args_to_patch(parsed_args.parameters))
        patch.extend(utils.args_to_patch(parsed_args.flavors, roles, "Flavor"))
        patch.extend(utils.args_to_patch(parsed_args.scales, roles, "count"))

        if len(patch) > 0:
            plan = client.plans.patch(parsed_args.plan_uuid, patch)
        else:
            print(("WARNING: No valid arguments passed. No update operation "
                   "has been performed."), file=sys.stderr)

        return self.dict2columns(plan.to_dict())


class ShowManagementPlan(show.ShowOne):
    """Show a Management Plan."""

    log = logging.getLogger(__name__ + '.ShowManagementPlan')

    def get_parser(self, prog_name):
        parser = super(ShowManagementPlan, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan to show."
        )

        parser.add_argument(
            '--long', default=False, action="store_true",
            help="Display full plan details"
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management
        plan = client.plans.get(parsed_args.plan_uuid)
        plan_dict = plan.to_dict()

        if not parsed_args.long:
            if 'parameters' in plan_dict:
                plan_dict['parameters'] = ("Parameter output suppressed. Use "
                                           "--long to display them.")
            plan_dict['roles'] = ', '.join([r.name for r in plan.roles])

        return self.dict2columns(plan_dict)


class AddManagementPlanRole(show.ShowOne):
    """Add a Role to a Management Plan."""

    log = logging.getLogger(__name__ + '.AddManagementPlanRole')

    def get_parser(self, prog_name):
        parser = super(AddManagementPlanRole, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan."
        )

        parser.add_argument(
            'role_uuid',
            help="The UUID of the Role being added to the Plan."
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        plan = client.plans.add_role(
            parsed_args.plan_uuid,
            parsed_args.role_uuid
        )

        return self.dict2columns(filtered_plan_dict(plan.to_dict()))


class RemoveManagementPlanRole(show.ShowOne):
    """Remove a Role from a Management Plan."""

    log = logging.getLogger(__name__ + '.RemoveManagementPlanRole')

    def get_parser(self, prog_name):
        parser = super(RemoveManagementPlanRole, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan."
        )

        parser.add_argument(
            'role_uuid',
            help="The UUID of the Role being removed from the Plan."
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        plan = client.plans.remove_role(
            parsed_args.plan_uuid,
            parsed_args.role_uuid
        )

        return self.dict2columns(filtered_plan_dict(plan.to_dict()))


class DownloadManagementPlan(command.Command):
    """Download a Management Plan."""

    log = logging.getLogger(__name__ + '.DownloadManagementPlan')

    def get_parser(self, prog_name):
        parser = super(DownloadManagementPlan, self).get_parser(prog_name)

        parser.add_argument(
            'plan_uuid',
            help="The UUID of the plan to download."
        )

        parser.add_argument(
            '-O', '--output-dir', metavar='<OUTPUT DIR>',
            required=True,
            help=('Directory to write template files into. It will be created '
                  'if it does not exist and any existing files in the '
                  'directory will be removed.')
        )

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)" % parsed_args)

        client = self.app.client_manager.management

        output_dir = parsed_args.output_dir

        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

        os.mkdir(output_dir)

        # retrieve templates
        templates = client.plans.templates(parsed_args.plan_uuid)

        # write file for each key-value in templates
        print("The following templates will be written:")
        for template_name, template_content in templates.items():

            # It's possible to organize the role templates and their dependent
            # files into directories, in which case the template_name will
            # carry the directory information. If that's the case, first
            # create the directory structure (if it hasn't already been
            # created by another file in the templates list).
            template_dir = os.path.dirname(template_name)
            output_template_dir = os.path.join(output_dir, template_dir)
            if template_dir and not os.path.exists(output_template_dir):
                os.makedirs(output_template_dir)

            filename = os.path.join(output_dir, template_name)
            with open(filename, 'w+') as template_file:
                template_file.write(template_content)
            print(filename)


def filtered_plan_dict(plan_dict):
    if 'parameters' in plan_dict and 'roles' in plan_dict:
            plan_dict['parameters'] = [param for param in
                                       plan_dict['parameters']
                                       if param['name'].endswith('::count')]

            plan_dict['parameters'] = formatting.parameters_v2_formatter(
                plan_dict['parameters'])

            plan_dict['roles'] = formatting.parameters_v2_formatter(
                plan_dict['roles'])

    return plan_dict
