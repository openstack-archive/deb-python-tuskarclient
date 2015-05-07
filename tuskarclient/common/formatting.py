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

from __future__ import print_function

import sys

import prettytable


def attributes_formatter(attributes):
    """Given a simple dict format the keyvalue pairs with one on each line.
    """
    return u"".join(u"{0}={1}\n".format(k, v) for k, v in
                    sorted(attributes.items()))


def parameters_v2_formatter(parameters):
    """Given a list of dicts format parameters output."""
    return u"\n".join(attributes_formatter(parameter)
                      for parameter in parameters)


def list_plan_roles_formatter(roles):
    """Given a list of Roles format roles' names into row."""
    return u", ".join(role.name for role in roles)


def print_list(objs, fields, formatters={}, custom_labels={}, sortby=0,
               outfile=sys.stdout):
    '''Prints a list of objects.

    :param objs: list of objects to print
    :param fields: list of attributes of the objects to print;
        attributes beginning with '!' have a special meaning - they
        should be used with custom field labels and formatters only,
        and the formatter receives the whole object
    :param formatters: dict of functions that perform pre-print
        formatting of attributes (keys are strings from `fields`
        parameter, values are functions that take one parameter - the
        attribute)
    :param custom_labels: dict of label overrides for fields (keys are
        strings from `fields` parameter, values are custom labels -
        headers of the table)
    '''
    field_labels = [custom_labels.get(f, f) for f in fields]
    pt = prettytable.PrettyTable([f for f in field_labels],
                                 caching=False, print_empty=False)
    pt.align = 'l'

    for o in objs:
        row = []
        for field in fields:
            if field[0] == '!':  # custom field
                if field in formatters:
                    row.append(formatters[field](o))
                else:
                    raise KeyError(
                        'Custom field "%s" needs a formatter.' % field)
            else:  # attribute-based field
                if hasattr(o, field) and field in formatters:
                    row.append(formatters[field](getattr(o, field)))
                else:
                    row.append(getattr(o, field, ''))
        pt.add_row(row)
    print(pt.get_string(sortby=field_labels[sortby]), file=outfile)


def print_dict(d, formatters={}, custom_labels={}, outfile=sys.stdout):
    '''Prints a dict to the provided file or file-like object.

    :param d: dict to print
    :param formatters: dict of functions that perform pre-print
        formatting of dict values (keys are keys from `d` parameter,
        values are functions that take one parameter - the dict value
        to format). A wild card formatter can be provided as '*' which
        will be applied to all fields without a dedicated formatter.
    :param custom_labels: dict of label overrides for keys (keys are
        keys from `d` parameter, values are custom labels)
    '''
    pt = prettytable.PrettyTable(['Property', 'Value'],
                                 caching=False, print_empty=False)
    pt.align = 'l'

    global_formatter = formatters.get('*')

    for field in d.keys():
        label = custom_labels.get(field, field)
        if field in formatters:
            pt.add_row([label, formatters[field](d[field])])
        elif global_formatter:
            pt.add_row([label, global_formatter(d[field])])
        else:
            pt.add_row([label, d[field]])
    print(pt.get_string(sortby='Property'), file=outfile)
