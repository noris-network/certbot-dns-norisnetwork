"""DNS Authenticator for noris network."""
import json
import logging

from typing import Any, Callable, Dict, Optional, Tuple

import requests

from certbot import errors
from certbot.plugins import dns_common

logger = logging.getLogger(__name__)

API_BASE_PATH = "https://service-api.noris.net/v1/api"


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for noris network.

    This Authenticator uses the noris network Service API to fulfill a dns-01 challenge.
    """

    description = (
        "Obtain certificates using a DNS TXT record (if you use noris network for DNS)."
    )
    ttl = 30

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: Optional[dns_common.CredentialsConfiguration] = None

    @classmethod
    def add_parser_arguments(
        cls, add: Callable[..., None], default_propagation_seconds: int = 60
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="ServiceAPI credentials INI file.")

    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a dns-01 challenge using noris network Service API."  # pylint: disable=line-too-long

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "ServiceAPI credentials INI file",
            {"token": "noris API Token"},
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_serviceapi_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_serviceapi_client().del_txt_record(
            domain, validation_name, validation
        )

    def _get_serviceapi_client(self) -> "_ServiceAPIClient":
        if not self.credentials:
            raise errors.PluginError("Plugin has not been prepared.")
        return _ServiceAPIClient(self.credentials.conf("token"))


class _ServiceAPIClient:
    """
    Encapsulates all communication with the Service API.
    """

    def __init__(self, token: str) -> None:
        logger.debug("Creating ServiceAPIClient")
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "X-noris-API-Token": self.token,
        }

    def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = self._get_url(endpoint)
        resp = requests.request(
            method, url, headers=self.headers, json=data, params=params, timeout=120
        )
        logger.debug("API %s Request to URL: %s", method, url)

        if resp.status_code >= 400:
            raise errors.PluginError(
                f"HTTP Error during API request at {url} with status code: {resp.status_code}"
            )

        try:
            response = resp.json()
        except json.decoder.JSONDecodeError as exc:
            raise errors.PluginError(f"{exc}: API response with non JSON: {resp.text}")
        return response

    def _get_url(self, endpoint: str) -> str:
        return API_BASE_PATH + endpoint

    def _get_record_name(self, record_name, zone_name):
        return record_name.replace(zone_name, "").rstrip(".")

    def add_txt_record(
        self, domain: str, record_name: str, record_content: str, record_ttl: int
    ) -> None:
        """
        Add a TXT record using the supplied information.

        :param str domain: The domain to use to look up the DNS zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the Service API
        """
        try:
            zone_id, zone_name, _ = self._find_managed_zone_id(domain)
            logger.info("Domain found: DNS zone with id %s", zone_id)
        except errors.PluginError as exc:
            logger.error("Error finding DNS zone using the Service API: %s", exc)
            raise

        original_record_name = record_name
        record_name = self._get_record_name(record_name, zone_name)
        logger.info(
            "Using record_name: %s from original: %s", record_name, original_record_name
        )

        logger.info("Insert new TXT record with name %s.", record_name)
        self._insert_txt_record(zone_id, record_name, record_content, record_ttl)

    def del_txt_record(
        self, domain: str, record_name: str, record_content: str
    ) -> None:
        """
        Delete a TXT record using the supplied information.

        :param str domain: The domain to use to look up the managed zone.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record value normalized with double quotes.
        :raises certbot.errors.PluginError: if an error occurs communicating with the ISPConfig API
        """
        try:
            zone_id, zone_name, dns_rrs_endpoint = self._find_managed_zone_id(domain)
            logger.info("Domain found: DNS zone with id %s", zone_id)
        except errors.PluginError as exc:
            logger.error("Error finding DNS zone using the Service API: %s", exc)
            raise

        original_record_name = record_name
        record_name = self._get_record_name(record_name, zone_name)
        logger.info(
            "Using record_name: %s from original: %s", record_name, original_record_name
        )

        record = self.get_existing_txt_rrs(
            dns_rrs_endpoint, record_name, record_content
        )

        if record is not None:
            logger.info("Delete TXT record with ID: %s", record["id"])
            self._delete_txt_record(zone_id, record["id"])

    def _prepare_rr_data(
        self, record_name: str, record_content: str, record_ttl: int
    ) -> Dict[str, Any]:
        rr_data = {
            "_attributes": {
                "_log_message": "dns-01 challenge",
                "_delete": [],
                "_create": [
                    {
                        "name": record_name,
                        "type": "TXT",
                        "ttl": record_ttl,
                        "rdata": f'"{record_content}"',
                    }
                ],
            }
        }
        return rr_data

    def _insert_txt_record(
        self, zone_id: int, record_name: str, record_content: str, record_ttl: int
    ) -> None:
        rr_data = self._prepare_rr_data(record_name, record_content, record_ttl)
        endpoint = f"/data/dns/zone/{zone_id}/"
        self._api_request("PATCH", endpoint, rr_data)

    def _delete_txt_record(self, zone_id: int, dns_rr_id: int) -> None:
        del_data = {
            "_attributes": {
                "_create": [],
                "_delete": [{"id": dns_rr_id}],
                "_log_message": "dns-01 challenge delete",
            }
        }
        endpoint = f"/data/dns/zone/{zone_id}/"
        self._api_request("PATCH", endpoint, del_data)

    def _find_managed_zone_id(self, domain: str) -> Tuple[int, str, str]:
        """
        Find the DNS zone for a given domain.

        :param str domain: The domain for which to find the managed zone.
        :returns: The ID of the managed zone, if found.
        :rtype: str
        :raises certbot.errors.PluginError: if the DNS zone cannot be found.
        """

        logger.info("Looking for the DNS zone of domain: %s.", domain)
        try:
            zone_info = self._api_request(
                "GET",
                "/data/dns/zone/",
                params={"_query": json.dumps({"for_fqdn": domain})},
            )
            zone_id = zone_info["_data"][0]["id"]
            zone_name = zone_info["_data"][0]["name_idna"]
            dns_rrs_endpoint = zone_info["_data"][0]["_links"][0]["href"]
        except IndexError as exc:
            # An API request for a domain that is not managed either by the user
            # or by noris returns a successful (status_code 200), but empty response.
            # e.g. {"data": [], "recordsFiltered": 0}
            logger.warning("%s: Domain %s not related to a known DNS zone", exc, domain)
            raise errors.PluginError(
                f"Unable to determine managed DNS zone for {domain}."
            )

        return zone_id, zone_name, dns_rrs_endpoint

    def get_existing_txt_rrs(
        self, endpoint: str, record_name: str, record_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing TXT records from the RRset for the record name.

        If an error occurs while requesting the record set, it is suppressed
        and None is returned.

        :param str endpoint: The endpoint to get DNS RRs for the specific zone ID.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record value normalized with double quotes.

        :returns: TXT record value or None
        :rtype: `string` or `None`

        """

        dns_rrs = self._api_request("GET", endpoint)["_data"]

        for record in dns_rrs:
            if (
                record["name_prefix"] == record_name
                and record["dns_rr_type"]["_title"] == "TXT"
                and record["rdata"] == f'"{record_content}"'
            ):
                return record
        return None
