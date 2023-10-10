# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

from keystone.conf import utils

group_url = cfg.StrOpt(
    'group_url',
    default='...',
    help=utils.fmt("""
Keycloak admin URL
"""))

token_url = cfg.StrOpt(
    'token_url',
    default='...',
    help=utils.fmt("""
Keycloak token URL
"""))

client_id = cfg.StrOpt(
    'client_id',
    default='...',
    help=utils.fmt("""
client id
"""))

client_secret = cfg.StrOpt(
    'client_secret',
    default='...',
    help=utils.fmt("""
Client secret
"""))


GROUP_NAME = __name__.split('.')[-1]
ALL_OPTS = [
    group_url,
    token_url,
    client_id,
    client_secret,
]


def register_opts(conf):
    conf.register_opts(ALL_OPTS, group=GROUP_NAME)


def list_opts():
    return {GROUP_NAME: ALL_OPTS}
