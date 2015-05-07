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
from keystoneclient.v2_0 import client as ksclient

from tuskarclient.openstack.common.apiclient import auth
from tuskarclient.openstack.common.apiclient import exceptions


class KeystoneAuthPlugin(auth.BaseAuthPlugin):
    opt_names = [
        "username",
        "password",
        "tenant_id",
        "tenant_name",
        "token",
        "auth_url",
        "endpoint",
    ]

    def _do_authenticate(self, httpclient):
        if self.opts.get('token') is None:
            ks_kwargs = {
                'username': self.opts.get('username'),
                'password': self.opts.get('password'),
                'tenant_id': self.opts.get('tenant_id'),
                'tenant_name': self.opts.get('tenant_name'),
                'auth_url': self.opts.get('auth_url'),
            }

            self._ksclient = ksclient.Client(**ks_kwargs)

    def token_and_endpoint(self, endpoint_type, service_type):
        token = endpoint = None

        if self.opts.get('token') and self.opts.get('endpoint'):
            token = self.opts.get('token')
            endpoint = self.opts.get('endpoint')
        elif hasattr(self, '_ksclient'):
            token = self._ksclient.auth_token
            endpoint = (self.opts.get('endpoint') or
                        self._ksclient.service_catalog.url_for(
                            service_type=service_type or 'management',
                            endpoint_type=endpoint_type))

        return (token, endpoint)

    def sufficient_options(self):
        """Check if all required options are present.

        :raises: AuthPluginOptionsMissing
        """
        if self.opts.get('token'):
            lookup_table = ["token", "endpoint"]
        else:
            lookup_table = [
                "username",
                "password",
                "auth_url"
            ]
            tenant_opts = ["tenant_id", "tenant_name"]
            if not any([self.opts.get(opt) for opt in tenant_opts]):
                raise exceptions.AuthPluginOptionsMissing(
                    ' or '.join(tenant_opts))

        missing = [opt for opt in lookup_table if not self.opts.get(opt)]
        if missing:
            raise exceptions.AuthPluginOptionsMissing(missing)
