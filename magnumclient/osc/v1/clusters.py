# Copyright 2016 EasyStack.  All rights reserved.
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

import os

from magnumclient.common import utils as magnum_utils
from magnumclient import exceptions
from magnumclient.i18n import _

from osc_lib.command import command
from osc_lib import utils


CLUSTER_ATTRIBUTES = [
    'status',
    'cluster_template_id',
    'node_addresses',
    'uuid',
    'stack_id',
    'status_reason',
    'created_at',
    'updated_at',
    'coe_version',
    'labels',
    'faults',
    'keypair',
    'api_address',
    'master_addresses',
    'create_timeout',
    'node_count',
    'discovery_url',
    'master_count',
    'container_version',
    'name',
    'master_flavor_id',
    'flavor_id',
]


class CreateCluster(command.Command):
    _description = _("Create a cluster")

    def get_parser(self, prog_name):
        parser = super(CreateCluster, self).get_parser(prog_name)
        # NOTE: All arguments are positional and, if not provided
        # with a default, required.
        parser.add_argument('--cluster-template',
                            dest='cluster_template',
                            required=True,
                            metavar='<cluster-template>',
                            help='ID or name of the cluster template.')
        parser.add_argument('--discovery-url',
                            dest='discovery_url',
                            metavar='<discovery-url>',
                            help=('Specifies custom delivery url for '
                                  'node discovery.'))
        parser.add_argument('--docker-volume-size',
                            dest='docker_volume_size',
                            type=int,
                            metavar='<docker-volume-size>',
                            help=('The size in GB for the docker volume to '
                                  'use.'))
        parser.add_argument('--labels',
                            metavar='<KEY1=VALUE1,KEY2=VALUE2;KEY3=VALUE3...>',
                            action='append',
                            help=_('Arbitrary labels in the form of key=value'
                                   'pairs to associate with a cluster '
                                   'template. May be used multiple times.'))
        parser.add_argument('--keypair',
                            default=None,
                            metavar='<keypair>',
                            help='UUID or name of the keypair to use.')
        parser.add_argument('--master-count',
                            dest='master_count',
                            type=int,
                            default=1,
                            metavar='<master-count>',
                            help='The number of master nodes for the cluster.')
        parser.add_argument('name',
                            metavar='<name>',
                            help='Name of the cluster to create.')
        parser.add_argument('--node-count',
                            dest='node_count',
                            type=int,
                            default=1,
                            metavar='<node-count>',
                            help='The cluster node count.')
        parser.add_argument('--timeout',
                            type=int,
                            default=60,
                            metavar='<timeout>',
                            help=('The timeout for cluster creation time. The '
                                  'default is 60 minutes.'))
        parser.add_argument(
            '--master-flavor',
            dest='master_flavor',
            metavar='<master-flavor>',
            help=_('The nova flavor name or UUID to use when launching the '
                   'master node of the Cluster.'))
        parser.add_argument(
            '--flavor',
            metavar='<flavor>',
            help=_('The nova flavor name or UUID to use when launching the '
                   'Cluster.'))

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)", parsed_args)

        mag_client = self.app.client_manager.container_infra
        args = {
            'cluster_template_id': parsed_args.cluster_template,
            'create_timeout': parsed_args.timeout,
            'discovery_url': parsed_args.discovery_url,
            'docker_volume_size': parsed_args.docker_volume_size,
            'keypair': parsed_args.keypair,
            'master_count': parsed_args.master_count,
            'name': parsed_args.name,
            'node_count': parsed_args.node_count,
            'master_flavor_id': parsed_args.master_flavor,
            'flavor_id': parsed_args.flavor,
        }

        if parsed_args.labels is not None:
            args['labels'] = magnum_utils.handle_labels(parsed_args.labels)

        cluster = mag_client.clusters.create(**args)
        print("Request to create cluster %s accepted"
              % cluster.uuid)


class DeleteCluster(command.Command):
    _description = _("Delete a cluster")

    def get_parser(self, prog_name):
        parser = super(DeleteCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            nargs='+',
            metavar='<cluster>',
            help='ID or name of the cluster(s) to delete.')

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)", parsed_args)

        mag_client = self.app.client_manager.container_infra
        for cluster in parsed_args.cluster:
            mag_client.clusters.delete(cluster)
            print("Request to delete cluster %s has been accepted." % cluster)


class ListCluster(command.Lister):
    _description = _("List clusters")

    def get_parser(self, prog_name):
        parser = super(ListCluster, self).get_parser(prog_name)

        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            help=_('Maximum number of clusters to return'))
        parser.add_argument(
            '--sort-key',
            metavar='<sort-key>',
            help=_('Column to sort results by'))
        parser.add_argument(
            '--sort-dir',
            metavar='<sort-dir>',
            choices=['desc', 'asc'],
            help=_('Direction to sort. "asc" or "desc".'))

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)", parsed_args)

        mag_client = self.app.client_manager.container_infra
        columns = [
            'uuid', 'name', 'keypair', 'node_count', 'master_count', 'status']
        clusters = mag_client.clusters.list(limit=parsed_args.limit,
                                            sort_key=parsed_args.sort_key,
                                            sort_dir=parsed_args.sort_dir)
        return (
            columns,
            (utils.get_item_properties(c, columns) for c in clusters)
        )


class ShowCluster(command.ShowOne):
    _description = _("Show a Cluster")

    def get_parser(self, prog_name):
        parser = super(ShowCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('ID or name of the cluster to show.')
            )
        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)", parsed_args)

        columns = CLUSTER_ATTRIBUTES

        mag_client = self.app.client_manager.container_infra
        cluster = mag_client.clusters.get(parsed_args.cluster)

        return (columns, utils.get_item_properties(cluster, columns))


class UpdateCluster(command.Command):
    _description = _("Update a Cluster")

    def get_parser(self, prog_name):
        parser = super(UpdateCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('The name or UUID of cluster to update'))

        parser.add_argument(
            'op',
            metavar='<op>',
            choices=['add', 'replace', 'remove'],
            help=_("Operations: one of 'add', 'replace' or 'remove'"))

        parser.add_argument(
            'attributes',
            metavar='<path=value>',
            nargs='+',
            action='append',
            default=[],
            help=_(
                "Attributes to add/replace or remove (only PATH is necessary "
                "on remove)"))

        parser.add_argument(
            '--rollback',
            action='store_true',
            dest='rollback',
            default=False,
            help=_('Rollback cluster on update failure.'))

        return parser

    def take_action(self, parsed_args):
        self.log.debug("take_action(%s)", parsed_args)

        mag_client = self.app.client_manager.container_infra

        patch = magnum_utils.args_array_to_patch(parsed_args.op,
                                                 parsed_args.attributes[0])

        mag_client.clusters.update(parsed_args.cluster,
                                   patch)
        print("Request to update cluster %s has been accepted." %
              parsed_args.cluster)


class ConfigCluster(command.Command):
    _description = _("Get Configuration for a Cluster")

    def get_parser(self, prog_name):
        parser = super(ConfigCluster, self).get_parser(prog_name)
        parser.add_argument(
            'cluster',
            metavar='<cluster>',
            help=_('The name or UUID of cluster to update'))
        parser.add_argument(
            '--dir',
            metavar='<dir>',
            default='.',
            help=_('Directory to save the certificate and config files.'))
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help=_('Overwrite files if existing.'))

        return parser

    def take_action(self, parsed_args):
        """Configure native client to access cluster.

        You can source the output of this command to get the native client of
        the corresponding COE configured to access the cluster.

        """
        self.log.debug("take_action(%s)", parsed_args)

        mag_client = self.app.client_manager.container_infra

        parsed_args.dir = os.path.abspath(parsed_args.dir)
        cluster = mag_client.clusters.get(parsed_args.cluster)
        if cluster.status not in ('CREATE_COMPLETE', 'UPDATE_COMPLETE',
                                  'ROLLBACK_COMPLETE'):
            raise exceptions.CommandError("cluster in status %s" %
                                          cluster.status)
        cluster_template = mag_client.cluster_templates.get(
            cluster.cluster_template_id)
        opts = {
            'cluster_uuid': cluster.uuid,
        }

        if not cluster_template.tls_disabled:
            tls = magnum_utils.generate_csr_and_key()
            tls['ca'] = mag_client.certificates.get(**opts).pem
            opts['csr'] = tls['csr']
            tls['cert'] = mag_client.certificates.create(**opts).pem
            for k in ('key', 'cert', 'ca'):
                fname = "%s/%s.pem" % (parsed_args.dir, k)
                if os.path.exists(fname) and not parsed_args.force:
                    raise Exception("File %s exists, aborting." % fname)
                else:
                    f = open(fname, "w")
                    f.write(tls[k])
                    f.close()

        print(magnum_utils.config_cluster(cluster,
                                          cluster_template,
                                          parsed_args.dir,
                                          force=parsed_args.force))