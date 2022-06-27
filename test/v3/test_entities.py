import unittest
from http import HTTPStatus
from unittest.mock import MagicMock

from abstract_test_case import AbstractTestCase
from cloudfoundry_client.v3.entities import EntityManager


class TestEntities(unittest.TestCase, AbstractTestCase):
    def test_len(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/something")

        client.get.return_value = self.mock_response("/fake/something", HTTPStatus.OK, None, "v3", "apps", "GET_response.json")
        cpt = len(entity_manager)
        client.get.assert_called_with(client.get.return_value.url)

        self.assertEqual(cpt, 3)

