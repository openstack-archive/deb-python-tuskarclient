# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
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
Base utilities to build API operation managers and objects on top of.
"""

# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)


def getid(obj):
    """Abstracts the common pattern of allowing both an object or an
    object's ID (UUID) as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class Manager(object):
    """Managers interact with a particular type of API
    (samples, meters, alarms, etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api

    @staticmethod
    def _path(id=None):
        """Helper method to be defined in subclasses. It returns the
        resource/collection path. If id is given, then single resource
        path is returned. Otherwise the collection path is returned.

        :param id: id of the resource (optional)
        :type id: string

        :return: A string representing the API endpoint
        :rtype: string
        """
        raise NotImplementedError("_path method not implemented.")

    def _single_path(self, id):
        """This is like the _path method, but it asserts that the id
        parameter is not None. This is useful e.g. when you want to make sure
        that you can't issue a DELETE request on a collection URL.

        :param id: id of the resource (not optional)
        :type id: string

        :return: A string representing the API endpoint
        :rtype: string
        """
        if not id:
            raise ValueError("{0} id is required."
                             .format(self.resource_class))
        return self._path(id)

    def _create(self, url, body):
        resp, body = self.api.json_request('POST', url, body=body)
        if body:
            return self.resource_class(self, body)

    def _get(self, url, **kwargs):
        kwargs.setdefault('expect_single', True)
        try:
            return self._list(url, **kwargs)[0]
        except IndexError:
            return None

    def _list(self, url, response_key=None, obj_class=None, body=None,
              expect_single=False):
        resp, body = self.api.json_request('GET', url)

        if obj_class is None:
            obj_class = self.resource_class

        if response_key:
            try:
                data = body[response_key]
            except KeyError:
                return []
        else:
            data = body
        if expect_single:
            data = [data]
        return [obj_class(self, res, loaded=True) for res in data if res]

    def _update(self, url, body, response_key=None):
        resp, body = self.api.json_request('PUT', url, body=body)
        # PUT requests may not return a body
        if body:
            return self.resource_class(self, body)

    def _delete(self, url):
        self.api.raw_request('DELETE', url)
