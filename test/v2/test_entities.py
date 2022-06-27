import unittest
from functools import reduce
from http import HTTPStatus
from unittest.mock import MagicMock, call

from abstract_test_case import AbstractTestCase
from cloudfoundry_client.errors import InvalidEntity
from cloudfoundry_client.v2.entities import EntityManager


class TestEntities(unittest.TestCase, AbstractTestCase):
    def test_invalid_entity_without_entity_attribute(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/anyone")

        client.get.return_value = self.mock_response(
            "/fake/anyone/any-id", HTTPStatus.OK, None, "fake", "GET_invalid_entity_without_entity.json"
        )

        self.assertRaises(InvalidEntity, lambda: entity_manager["any-id"])

    def test_invalid_entity_with_null_entity(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/anyone")

        client.get.return_value = self.mock_response(
            "/fake/anyone/any-id", HTTPStatus.OK, None, "fake", "GET_invalid_entity_with_null_entity.json"
        )

        self.assertRaises(InvalidEntity, lambda: entity_manager["any-id"])

    def test_invalid_entity_with_invalid_entity_type(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/anyone")

        client.get.return_value = self.mock_response(
            "/fake/anyone/any-id", HTTPStatus.OK, None, "fake", "GET_invalid_entity_with_invalid_entity_type.json"
        )

        self.assertRaises(InvalidEntity, lambda: entity_manager["any-id"])

    def test_query(self):
        url = EntityManager("http://cf.api", None, "/v2/apps")._get_url_filtered(
            "/v2/apps", **{"results-per-page": 20, "order-direction": "asc", "page": 1, "space_guid": "id", "order-by": "id"}
        )
        self.assertEqual("/v2/apps?order-by=id&order-direction=asc&page=1&results-per-page=20&q=space_guid%3Aid", url)

    def test_query_multi_order_by(self):
        url = EntityManager("http://cf.api", None, "/v2/apps")._get_url_filtered("/v2/apps", **{"order-by": ["timestamp", "id"]})
        self.assertEqual("/v2/apps?order-by=timestamp&order-by=id", url)

    def test_query_single_order_by(self):
        url = EntityManager("http://cf.api", None, "/v2/apps")._get_url_filtered("/v2/apps", **{"order-by": "timestamp"})
        self.assertEqual("/v2/apps?order-by=timestamp", url)

    def test_query_in(self):
        url = EntityManager("http://cf.api", None, "/v2/apps")._get_url_filtered(
            "/v2/apps", **{"results-per-page": 20, "order-direction": "asc", "page": 1, "space_guid": ["id1", "id2"]}
        )
        self.assertEqual("/v2/apps?order-direction=asc&page=1&results-per-page=20&q=space_guid%20IN%20id1%2Cid2", url)

    def test_multi_query(self):
        url = EntityManager("http://cf.api", None, "/v2/events")._get_url_filtered(
            "/v2/events", **{"type": ["create", "update"], "organization_guid": "org-id"}
        )
        self.assertEqual("/v2/events?q=organization_guid%3Aorg-id&q=type%20IN%20create%2Cupdate", url)

    def test_range_query(self):
        url = EntityManager("http://cf.api", None, "/v2/events")._get_url_filtered(
            "/v2/events", **{"type": "app.crash", "space_guid": "space-id", "timestamp": {">": "2022-02-08T16:41:25Z"}}
        )
        self.assertEqual("/v2/events?q=space_guid%3Aspace-id&q=timestamp%3E2022-02-08T16%3A41%3A25Z&q=type%3Aapp.crash", url)

    def test_list(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/first")

        first_response = self.mock_response(
            "/fake/first?order-direction=asc&page=1&results-per-page=20&q=space_guid%3Asome-id",
            HTTPStatus.OK,
            None,
            "fake",
            "GET_multi_page_0_response.json",
        )
        second_response = self.mock_response(
            "/fake/next?order-direction=asc&page=2&results-per-page=50",
            HTTPStatus.OK,
            None,
            "fake",
            "GET_multi_page_1_response.json",
        )

        client.get.side_effect = [first_response, second_response]
        cpt = reduce(
            lambda increment, _: increment + 1,
            entity_manager.list(**{"results-per-page": 20, "order-direction": "asc", "page": 1, "space_guid": "some-id"}),
            0,
        )
        client.get.assert_has_calls([call(first_response.url), call(second_response.url)], any_order=False)
        self.assertEqual(cpt, 3)

    def test_iter(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/something")

        client.get.return_value = self.mock_response("/fake/something", HTTPStatus.OK, None, "fake", "GET_response.json")
        cpt = reduce(lambda increment, _: increment + 1, entity_manager, 0)
        client.get.assert_called_with(client.get.return_value.url)

        self.assertEqual(cpt, 2)

    def test_get_elem(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/something")

        client.get.return_value = self.mock_response(
            "/fake/something/with-id", HTTPStatus.OK, None, "fake", "GET_{id}_response.json"
        )
        entity = entity_manager["with-id"]
        client.get.assert_called_with(client.get.return_value.url)

        self.assertEqual(entity["entity"]["name"], "name-423")

    def test_len(self):
        client = MagicMock()
        entity_manager = EntityManager(self.TARGET_ENDPOINT, client, "/fake/something")

        client.get.return_value = self.mock_response("/fake/something", HTTPStatus.OK, None, "fake", "GET_response.json")
        cpt = len(entity_manager)
        client.get.assert_called_with(client.get.return_value.url)

        self.assertEqual(cpt, 3)