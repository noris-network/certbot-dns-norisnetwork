# pylint: disable=protected-access
"""Tests for certbot_dns_norisnetwork.dns_noris."""

import unittest

from unittest import mock

import requests

from certbot import errors
from certbot.compat import os
from certbot.plugins import dns_test_common
from certbot.plugins.dns_test_common import DOMAIN
from certbot.tests import util as test_util

from certbot_dns_norisnetwork.dns_noris import Authenticator, _ServiceAPIClient

FAKE_TOKEN = "faketoken1234"


class AuthenticatorTest(
    test_util.TempDirTestCase, dns_test_common.BaseAuthenticatorTest
):
    """Test Class"""

    def setUp(self):
        super().setUp()

        path = os.path.join(self.tempdir, "file.ini")
        dns_test_common.write({"noris_token": FAKE_TOKEN}, path)

        self.config = mock.MagicMock(
            noris_credentials=path, noris_propagation_seconds=0
        )  # don't wait during tests

        self.auth = Authenticator(self.config, "noris")

        self.mock_client = mock.MagicMock()
        self.auth._get_serviceapi_client = mock.MagicMock(return_value=self.mock_client)

    @test_util.patch_display_util()
    def test_perform(self, unused_mock_get_utility):
        """Test .perform() method"""
        self.auth.perform([self.achall])

        expected = [
            mock.call.add_txt_record(
                DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)

    def test_cleanup(self):
        """Test .cleanup() method"""
        self.auth._attempt_cleanup = True
        self.auth.cleanup([self.achall])

        expected = [
            mock.call.del_txt_record(DOMAIN, "_acme-challenge." + DOMAIN, mock.ANY)
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)


class ServiceAPIClientTest(unittest.TestCase):
    """Test ServiceAPI Client"""

    record_prefix = "_acme-challenge"
    record_name = record_prefix + "." + DOMAIN
    record_content = "bar"
    record_ttl = 60

    def setUp(self):
        self.client = _ServiceAPIClient(FAKE_TOKEN)
        self.client._get_url = mock.MagicMock(
            return_value="fake.service.noris.net/api/endpoint/"
        )

    def test_add_txt_record(self):
        """Test add_txt_record method"""

        def api_response_helper_not_existing_rr(
            method, endpoint, data=None, params=None
        ):  # pylint: disable=unused-argument
            if method == "GET":
                if params:
                    # called by function _find_managed_zone_id
                    zone_info = {
                        "_data": [
                            {
                                "id": 123,
                                "name_idna": DOMAIN,
                                "name": DOMAIN,
                                "ttl": 86400,
                                "_title": DOMAIN,
                                "_target": "dns_zone",
                                "_links": [
                                    {
                                        "href": "/data/dns/record/?_query=%7B%22zone%22:%7B%22id%22:123%7D%7D",  # pylint: disable=line-too-long
                                        "rel": "record",
                                    }
                                ],
                            }
                        ],
                        "recordsFiltered": 1,
                    }
                    return zone_info
            elif method == "PATCH":
                # called by function _insert_txt_record or _del_txt_record
                pass
            return None

        self.client._api_request = mock.MagicMock(
            side_effect=api_response_helper_not_existing_rr
        )
        self.client.add_txt_record(
            DOMAIN, self.record_name, self.record_content, self.record_ttl
        )
        self.assertEqual(2, len(self.client._api_request.mock_calls))
        self.client._api_request.assert_any_call(
            "GET", "/data/dns/zone/", params={"_query": '{"for_fqdn": "example.com"}'}
        )
        self.client._api_request.assert_any_call(
            "PATCH",
            "/data/dns/zone/123/",
            {
                "_attributes": {
                    "_log_message": "dns-01 challenge",
                    "_delete": [],
                    "_create": [
                        {
                            "name": "_acme-challenge",
                            "type": "TXT",
                            "ttl": 60,
                            "rdata": '"bar"',
                        }
                    ],
                }
            },
        )

    def test_add_txt_record_fail_to_authenticate(self):
        """Test add_txt_record method when you get an HTTPUnauthorized error"""

        requests.request = mock.MagicMock()
        requests.request.return_value.status_code = 401
        self.assertRaises(
            errors.PluginError,
            self.client.add_txt_record,
            DOMAIN,
            self.record_name,
            self.record_content,
            self.record_ttl,
        )

    def test_add_txt_record_fail_to_find_domain(self):
        """
        Test add_txt_record method.
        Mock the_api_request with the response returned when a DNS zone cannot be found:
        i.e. it's not managed by nnIS
        """
        self.client._api_request = mock.MagicMock(
            return_value={"_data": [], "recordsFiltered": 0}
        )
        self.assertRaises(
            errors.PluginError,
            self.client.add_txt_record,
            DOMAIN,
            self.record_name,
            self.record_content,
            self.record_ttl,
        )

    def test_del_txt_record(self):
        """Test del_txt_record method"""

        def api_response_helper_existing_acme_rr(
            method,
            endpoint,
            data=None,
            params=None,
        ):  # pylint: disable=unused-argument
            if method == "GET":
                if params:
                    # called by function _find_managed_zone_id
                    zone_info = {
                        "_data": [
                            {
                                "id": 123,
                                "name_idna": DOMAIN,
                                "name": DOMAIN,
                                "ttl": 86400,
                                "_title": DOMAIN,
                                "_target": "dns_zone",
                                "_links": [
                                    {
                                        "href": "/data/dns/record/?_query=%7B%22zone%22:%7B%22id%22:123%7D%7D",  # pylint: disable=line-too-long
                                        "rel": "record",
                                    }
                                ],
                            }
                        ],
                        "recordsFiltered": 1,
                    }
                    return zone_info
                if "/data/dns/record/" in endpoint:
                    # called by function get_existing_txt_rrs
                    # returns an existing record
                    record = {
                        "_data": [
                            {
                                "id": 247,
                                "name_prefix": "_acme-challenge",
                                "zone": {
                                    "id": 123,
                                    "_target": "dns_zone",
                                    "_title": DOMAIN,
                                },
                                "dns_rr_type": {
                                    "id": 16,
                                    "_target": "dns_rr_type",
                                    "_title": "TXT",
                                },
                                "ttl": 60,
                                "mx_preference": None,
                                "rdata": f'"{self.record_content}"',
                                "effective_rdata": self.record_content,
                                "_title": f'_acme_challenge TXT "{self.record_content}"',
                                "_target": "dns_rr",
                            },
                        ],
                        "recordsFiltered": 1,
                    }
                    return record
            elif method == "PATCH":
                # called by function _insert_txt_record or _del_txt_record
                pass
            return None

        self.client._api_request = mock.MagicMock(
            side_effect=api_response_helper_existing_acme_rr
        )
        self.client.del_txt_record(DOMAIN, self.record_name, self.record_content)
        self.assertEqual(3, len(self.client._api_request.mock_calls))
        self.client._api_request.assert_any_call(
            "GET", "/data/dns/zone/", params={"_query": '{"for_fqdn": "example.com"}'}
        )
        self.client._api_request.assert_any_call(
            "GET", "/data/dns/record/?_query=%7B%22zone%22:%7B%22id%22:123%7D%7D"
        )
        self.client._api_request.assert_any_call(
            "PATCH",
            "/data/dns/zone/123/",
            {
                "_attributes": {
                    "_log_message": "dns-01 challenge delete",
                    "_delete": [{"id": 247}],
                    "_create": [],
                }
            },
        )

    def test_del_txt_record_fail_to_authenticate(self):
        """Test del_txt_record method when you get an HTTPUnauthorized error"""
        requests.request = mock.MagicMock()
        requests.request.return_value.status_code = 401
        type(requests.request).status_code = mock.PropertyMock(return_value=401)
        self.assertRaises(
            errors.PluginError,
            self.client.del_txt_record,
            DOMAIN,
            self.record_name,
            self.record_content,
        )

    def test_del_txt_record_fail_to_find_domain(self):
        """
        Test del_txt_record method.
        Mock the_api_request with the response returned when a DNS zone cannot be found.
        """
        self.client._api_request = mock.MagicMock(
            return_value={"_data": [], "recordsFiltered": 0}
        )
        self.assertRaises(
            errors.PluginError,
            self.client.del_txt_record,
            DOMAIN,
            self.record_name,
            self.record_content,
        )


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
