# -*- coding: utf-8 -*-
# Copyright 2014 IBM Corp.
#
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

import uuid

from testtools import matchers

from keystone.common import sql
from keystone.identity.mapping_backends import mapping
from keystone.tests import unit
from keystone.tests.unit import identity_mapping as mapping_sql
from keystone.tests.unit import test_backend_sql


class SqlIDMappingTable(test_backend_sql.SqlModels):
    """Set of tests for checking SQL Identity ID Mapping."""

    def test_id_mapping(self):
        cols = (('public_id', sql.String, 64),
                ('domain_id', sql.String, 64),
                ('local_id', sql.String, 64),
                ('entity_type', sql.Enum, None))
        self.assertExpectedSchema('id_mapping', cols)


class SqlIDMapping(test_backend_sql.SqlTests):

    def setUp(self):
        super(SqlIDMapping, self).setUp()
        self.load_sample_data()

    def load_sample_data(self):
        self.addCleanup(self.clean_sample_data)
        domainA = unit.new_domain_ref()
        self.domainA = self.resource_api.create_domain(domainA['id'], domainA)
        domainB = unit.new_domain_ref()
        self.domainB = self.resource_api.create_domain(domainB['id'], domainB)

    def clean_sample_data(self):
        if hasattr(self, 'domainA'):
            self.domainA['enabled'] = False
            self.resource_api.update_domain(self.domainA['id'], self.domainA)
            self.resource_api.delete_domain(self.domainA['id'])
        if hasattr(self, 'domainB'):
            self.domainB['enabled'] = False
            self.resource_api.update_domain(self.domainB['id'], self.domainB)
            self.resource_api.delete_domain(self.domainB['id'])

    def test_invalid_public_key(self):
        self.assertIsNone(self.id_mapping_api.get_id_mapping(uuid.uuid4().hex))

    def test_id_mapping_crud(self):
        initial_mappings = len(mapping_sql.list_id_mappings())
        local_id1 = uuid.uuid4().hex
        local_id2 = uuid.uuid4().hex
        local_entity1 = {'domain_id': self.domainA['id'],
                         'local_id': local_id1,
                         'entity_type': mapping.EntityType.USER}
        local_entity2 = {'domain_id': self.domainB['id'],
                         'local_id': local_id2,
                         'entity_type': mapping.EntityType.GROUP}

        # Check no mappings for the new local entities
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity1))
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity2))

        # Create the new mappings and then read them back
        public_id1 = self.id_mapping_api.create_id_mapping(local_entity1)
        public_id2 = self.id_mapping_api.create_id_mapping(local_entity2)
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 2))
        self.assertEqual(
            public_id1, self.id_mapping_api.get_public_id(local_entity1))
        self.assertEqual(
            public_id2, self.id_mapping_api.get_public_id(local_entity2))

        local_id_ref = self.id_mapping_api.get_id_mapping(public_id1)
        self.assertEqual(self.domainA['id'], local_id_ref['domain_id'])
        self.assertEqual(local_id1, local_id_ref['local_id'])
        self.assertEqual(mapping.EntityType.USER, local_id_ref['entity_type'])
        # Check we have really created a new external ID
        self.assertNotEqual(local_id1, public_id1)

        local_id_ref = self.id_mapping_api.get_id_mapping(public_id2)
        self.assertEqual(self.domainB['id'], local_id_ref['domain_id'])
        self.assertEqual(local_id2, local_id_ref['local_id'])
        self.assertEqual(mapping.EntityType.GROUP, local_id_ref['entity_type'])
        # Check we have really created a new external ID
        self.assertNotEqual(local_id2, public_id2)

        # Create another mappings, this time specifying a public ID to use
        new_public_id = uuid.uuid4().hex
        public_id3 = self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainB['id'], 'local_id': local_id2,
             'entity_type': mapping.EntityType.USER},
            public_id=new_public_id)
        self.assertEqual(new_public_id, public_id3)
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 3))

        # Delete the mappings we created, and make sure the mapping count
        # goes back to where it was
        self.id_mapping_api.delete_id_mapping(public_id1)
        self.id_mapping_api.delete_id_mapping(public_id2)
        self.id_mapping_api.delete_id_mapping(public_id3)
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings))

    def test_id_mapping_handles_unicode(self):
        initial_mappings = len(mapping_sql.list_id_mappings())
        local_id = u'fäké1'
        local_entity = {'domain_id': self.domainA['id'],
                        'local_id': local_id,
                        'entity_type': mapping.EntityType.USER}

        # Check no mappings for the new local entity
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity))

        # Create the new mapping and then read it back
        public_id = self.id_mapping_api.create_id_mapping(local_entity)
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 1))
        self.assertEqual(
            public_id, self.id_mapping_api.get_public_id(local_entity))

    def test_delete_public_id_is_silent(self):
        # Test that deleting an invalid public key is silent
        self.id_mapping_api.delete_id_mapping(uuid.uuid4().hex)

    def test_purge_mappings(self):
        initial_mappings = len(mapping_sql.list_id_mappings())
        local_id1 = uuid.uuid4().hex
        local_id2 = uuid.uuid4().hex
        local_id3 = uuid.uuid4().hex
        local_id4 = uuid.uuid4().hex
        local_id5 = uuid.uuid4().hex

        # Create five mappings,two in domainA, three in domainB
        self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainA['id'], 'local_id': local_id1,
             'entity_type': mapping.EntityType.USER})
        self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainA['id'], 'local_id': local_id2,
             'entity_type': mapping.EntityType.USER})
        public_id3 = self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainB['id'], 'local_id': local_id3,
             'entity_type': mapping.EntityType.GROUP})
        public_id4 = self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainB['id'], 'local_id': local_id4,
             'entity_type': mapping.EntityType.USER})
        public_id5 = self.id_mapping_api.create_id_mapping(
            {'domain_id': self.domainB['id'], 'local_id': local_id5,
             'entity_type': mapping.EntityType.USER})

        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 5))

        # Purge mappings for domainA, should be left with those in B
        self.id_mapping_api.purge_mappings(
            {'domain_id': self.domainA['id']})
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 3))
        self.id_mapping_api.get_id_mapping(public_id3)
        self.id_mapping_api.get_id_mapping(public_id4)
        self.id_mapping_api.get_id_mapping(public_id5)

        # Purge mappings for type Group, should purge one more
        self.id_mapping_api.purge_mappings(
            {'entity_type': mapping.EntityType.GROUP})
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 2))
        self.id_mapping_api.get_id_mapping(public_id4)
        self.id_mapping_api.get_id_mapping(public_id5)

        # Purge mapping for a specific local identifier
        self.id_mapping_api.purge_mappings(
            {'domain_id': self.domainB['id'], 'local_id': local_id4,
             'entity_type': mapping.EntityType.USER})
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings + 1))
        self.id_mapping_api.get_id_mapping(public_id5)

        # Purge mappings the remaining mappings
        self.id_mapping_api.purge_mappings({})
        self.assertThat(mapping_sql.list_id_mappings(),
                        matchers.HasLength(initial_mappings))

    def test_create_duplicate_mapping(self):
        local_entity = {
            'domain_id': self.domainA['id'],
            'local_id': uuid.uuid4().hex,
            'entity_type': mapping.EntityType.USER}
        public_id1 = self.id_mapping_api.create_id_mapping(local_entity)

        # second call should be successful and return the same
        # public_id as above
        public_id2 = self.id_mapping_api.create_id_mapping(local_entity)
        self.assertEqual(public_id1, public_id2)

        # even if public_id was specified, it should not be used,
        # and still the same public_id should be returned
        public_id3 = self.id_mapping_api.create_id_mapping(
            local_entity, public_id=uuid.uuid4().hex)
        self.assertEqual(public_id1, public_id3)

    @unit.skip_if_cache_disabled('identity')
    def test_cache_when_id_mapping_crud(self):
        local_id = uuid.uuid4().hex
        local_entity = {'domain_id': self.domainA['id'],
                        'local_id': local_id,
                        'entity_type': mapping.EntityType.USER}

        # Check no mappings for the new local entity
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity))

        # Create new mappings, and it should be in the cache after created
        public_id = self.id_mapping_api.create_id_mapping(local_entity)
        self.assertEqual(
            public_id, self.id_mapping_api.get_public_id(local_entity))
        local_id_ref = self.id_mapping_api.get_id_mapping(public_id)
        self.assertEqual(self.domainA['id'], local_id_ref['domain_id'])
        self.assertEqual(local_id, local_id_ref['local_id'])
        self.assertEqual(mapping.EntityType.USER, local_id_ref['entity_type'])

        # After delete the mapping, should be deleted from cache too
        self.id_mapping_api.delete_id_mapping(public_id)
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity))
        self.assertIsNone(self.id_mapping_api.get_id_mapping(public_id))

    @unit.skip_if_cache_disabled('identity')
    def test_invalidate_cache_when_purge_mappings(self):
        local_id1 = uuid.uuid4().hex
        local_id2 = uuid.uuid4().hex
        local_id3 = uuid.uuid4().hex
        local_id4 = uuid.uuid4().hex
        local_id5 = uuid.uuid4().hex

        # Create five mappings,two in domainA, three in domainB
        local_entity1 = {'domain_id': self.domainA['id'],
                         'local_id': local_id1,
                         'entity_type': mapping.EntityType.USER}
        local_entity2 = {'domain_id': self.domainA['id'],
                         'local_id': local_id2,
                         'entity_type': mapping.EntityType.USER}
        local_entity3 = {'domain_id': self.domainB['id'],
                         'local_id': local_id3,
                         'entity_type': mapping.EntityType.GROUP}
        local_entity4 = {'domain_id': self.domainB['id'],
                         'local_id': local_id4,
                         'entity_type': mapping.EntityType.USER}
        local_entity5 = {'domain_id': self.domainB['id'],
                         'local_id': local_id5,
                         'entity_type': mapping.EntityType.USER}

        self.id_mapping_api.create_id_mapping(local_entity1)
        self.id_mapping_api.create_id_mapping(local_entity2)
        self.id_mapping_api.create_id_mapping(local_entity3)
        self.id_mapping_api.create_id_mapping(local_entity4)
        self.id_mapping_api.create_id_mapping(local_entity5)

        # Purge mappings for domainA, should be left with those in B
        self.id_mapping_api.purge_mappings(
            {'domain_id': self.domainA['id']})
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity1))
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity2))

        # Purge mappings for type Group, should purge one more
        self.id_mapping_api.purge_mappings(
            {'entity_type': mapping.EntityType.GROUP})
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity3))

        # Purge mapping for a specific local identifier
        self.id_mapping_api.purge_mappings(
            {'domain_id': self.domainB['id'], 'local_id': local_id4,
             'entity_type': mapping.EntityType.USER})
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity4))

        # Purge mappings the remaining mappings
        self.id_mapping_api.purge_mappings({})
        self.assertIsNone(self.id_mapping_api.get_public_id(local_entity5))

    def test_get_domain_mapping_list(self):
        local_id1 = uuid.uuid4().hex
        local_id2 = uuid.uuid4().hex
        local_id3 = uuid.uuid4().hex
        local_id4 = uuid.uuid4().hex
        local_id5 = uuid.uuid4().hex

        # Create five mappings,two in domainA, three in domainB
        local_entity1 = {'domain_id': self.domainA['id'],
                         'local_id': local_id1,
                         'entity_type': mapping.EntityType.USER}
        local_entity2 = {'domain_id': self.domainA['id'],
                         'local_id': local_id2,
                         'entity_type': mapping.EntityType.USER}
        local_entity3 = {'domain_id': self.domainB['id'],
                         'local_id': local_id3,
                         'entity_type': mapping.EntityType.GROUP}
        local_entity4 = {'domain_id': self.domainB['id'],
                         'local_id': local_id4,
                         'entity_type': mapping.EntityType.USER}
        local_entity5 = {'domain_id': self.domainB['id'],
                         'local_id': local_id5,
                         'entity_type': mapping.EntityType.USER}

        local_entity1['public_id'] = self.id_mapping_api.create_id_mapping(
            local_entity1)
        local_entity2['public_id'] = self.id_mapping_api.create_id_mapping(
            local_entity2)
        local_entity3['public_id'] = self.id_mapping_api.create_id_mapping(
            local_entity3)
        local_entity4['public_id'] = self.id_mapping_api.create_id_mapping(
            local_entity4)
        local_entity5['public_id'] = self.id_mapping_api.create_id_mapping(
            local_entity5)

        # list mappings for domainA
        domain_a_mappings = self.id_mapping_api.get_domain_mapping_list(
            self.domainA['id'])
        domain_a_mappings = [m.to_dict() for m in domain_a_mappings]
        self.assertItemsEqual([local_entity1, local_entity2],
                              domain_a_mappings)
