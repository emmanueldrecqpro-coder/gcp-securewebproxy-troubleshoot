import fnmatch
from urllib.parse import urlparse
from typing import Optional
from certificate import get_certificate
from utils import Colors, print_check, print_fail, print_success

from google.cloud import network_services_v1
from google.cloud import network_security_v1
from google.api_core import gapic_v1

from google.cloud.network_services_v1.services.network_services import pagers


def get_gateway(project_id, location, gateway_name):
    """
    Retrieves a gateway by name using the Network Services API.

    Args:
        project_id (str): The ID of the Google Cloud project.
        location (str): The location of the gateway.
        gateway_name (str): The name of the gateway to retrieve.

    Returns:
        The gateway object or None if an error occurred."""

    # Create a client
    client = network_services_v1.NetworkServicesClient()

    # Initialize request argument(s)
    request = network_services_v1.GetGatewayRequest(
        name=f"projects/{project_id}/locations/{location}/gateways/{gateway_name}",
    )

    # Make the request
    try:
        return client.get_gateway(
            request=request, retry=gapic_v1.method.DEFAULT, timeout=10.0
        )
    except Exception as e:
        print_fail(f"An error occurred when getting gateway: {e}")
        raise


def list_gateways(project_id, location) -> pagers.ListGatewaysPager:
    """
    Lists all gateways in the specified project and location using the Network Services API.

    Args:
        project_id (str): The ID of the Google Cloud project.
        location (str): The location of the gateways to list.

    Returns:
        List of gateways or None if an error occurred.
    """
    # Create a client
    client = network_services_v1.NetworkServicesClient()

    # Initialize request argument(s)
    request = network_services_v1.ListGatewaysRequest(
        parent=f"projects/{project_id}/locations/{location}",
    )

    try:
        # Make the request
        gateways_list = client.list_gateways(
            request=request, retry=gapic_v1.method.DEFAULT, timeout=10.0
        )
        return gateways_list

    except Exception as e:
        print_fail(f"An error occurred when listing gateways: {e}")
        raise


def list_gateway_security_policy_rules(security_policy_path):
    """
    Lists all security policy rules for a given gateway security policy.

    Args:
        security_policy_path (str): The full resource path of the gateway security policy.
            Example: "projects/{project_id}/locations/{location}/gatewaySecurityPolicies/{policy_name}

    Returns:
        List of security policy rules or None if an error occurred.
    """

    # Create a client
    client = network_security_v1.NetworkSecurityClient()

    # Initialize request argument(s)
    request = network_security_v1.ListGatewaySecurityPolicyRulesRequest(
        parent=security_policy_path,
    )

    # Make the request
    try:
        return client.list_gateway_security_policy_rules(
            request=request, retry=gapic_v1.method.DEFAULT, timeout=10.0
        )
    except Exception as e:
        print_fail(f"An error occurred when listing gateway security policy rules: {e}")
        raise


def get_gateway_based_on_hostname(
    project_id, location, hostname
) -> network_services_v1.Gateway:
    """
    Retrieves the gateway that matches the provided hostname.

    Args:
        project_id (str): The ID of the Google Cloud project.
        location (str): The location of the gateways to search.
        hostname (str): The hostname to match against gateway certificate SAN DNS names.

    Returns:
        The gateway object that matches the hostname or None if not found or an error occurred.
    """

    print_check(f"Searching for a gateway matching hostname '{hostname}'")

    try:
        gateways_list = list_gateways(project_id, location)

        if not gateways_list:
            print_fail("No gateways found in the project/location.", fatal=True)
            raise Exception("No gateways found")

        for gateway in gateways_list:
            for cert_url in gateway.certificate_urls:
                gateway_certificate = get_certificate(
                    cert_url.split("/")[1],
                    cert_url.split("/")[3],
                    cert_url.split("/")[5],
                )
                if hostname in gateway_certificate.san_dnsnames:
                    print_success(
                        f"Found gateway '{gateway.name.split('/')[-1]}' with a matching certificate SAN."
                    )
                    return gateway

        print_fail(
            f"No gateway found with a certificate SAN matching '{hostname}'.",
            fatal=True,
        )
        raise Exception("No gateway found")

    except Exception as e:
        print_fail(f"An error occurred when searching for gateway: {e}", fatal=True)
        raise


def check_security_policy_rules_for_subnet(
    gateway_security_policy_rules, subnet_cidr
) -> Optional[network_security_v1.GatewaySecurityPolicyRule]:
    """
    Checks if any of the gateway security policy rules match the instance subnet CIDR.

    Args:
        gateway_security_policy_rules: List of security policy rules to check.
        subnet_cidr: The CIDR range of the instance subnet to match against the rules.

    Returns:
        The matching security policy rule if found, otherwise None.
    """

    try:
        found_matching_rule = False
        print_check(
            f"Checking for a security policy rule matching instance subnet CIDR '{subnet_cidr}'"
        )

        for rule in gateway_security_policy_rules:
            if subnet_cidr in rule.session_matcher:
                print_success(
                    f"Rule '{rule.name.split('/')[-1]}' matches the instance subnet."
                )
                found_matching_rule = True
                return rule

        if not found_matching_rule:
            print_fail(
                f"No security policy rule found for source CIDR '{subnet_cidr}'."
            )
            return None

    except Exception as e:
        print_fail(f"An error occurred when checking security policy rules: {e}")
        return None


def check_gateway_certificate_hostname(gateway, hostname):
    """
    Checks if any of the gateway's certificate SAN DNS names match the provided hostname.

    Args:
        gateway: The gateway object containing certificate URLs.
        hostname: The hostname to match against the certificate SAN DNS names.

     Returns:
        True if a match is found, False otherwise.
    """

    try:

        # Check gateway certificate URLs and compare with the provided hostname
        for cert_url in gateway.certificate_urls:
            gateway_certificate = get_certificate(
                cert_url.split("/")[1],
                cert_url.split("/")[3],
                cert_url.split("/")[5],
            )
            if hostname == gateway_certificate.san_dnsnames[0]:
                print_success(
                    f"Hostname matches the certificate SAN DNS name: {gateway_certificate.san_dnsnames[0]}."
                )
                return True

        print_fail(
            "Hostname does NOT match the certificate SAN DNS name. This could be a configuration issue."
        )
        return False

    except Exception as e:
        print_fail(f"An error occurred when checking gateway certificate hostname: {e}")
        raise


def list_url_lists(swp_project_id, swp_location):
    """
    Lists all URL lists in the specified project and location using the Network Security API.

    Args:
        swp_project_id (str): The ID of the Google Cloud project where the SWP is deployed.
        swp_location (str): The location of the SWP.
    Returns:
        List of URL lists or None if an error occurred.
    """

    # Create a client
    client = network_security_v1.NetworkSecurityClient()

    try:
        # Initialize request argument(s)
        request = network_security_v1.ListUrlListsRequest(
            parent=f"projects/{swp_project_id}/locations/{swp_location}",
        )

        # Make the request
        return client.list_url_lists(request=request)

    except Exception as e:
        print_fail(f"An error occurred when initializing URL lists request: {e}")
        raise


def check_security_policy_rule_match_url_list(rule, url_lists):
    """
    Checks if the given security policy rule references any of the provided URL lists.

    Args:
        rule: The security policy rule to check.
        url_lists: The list of URL lists to check against.

    Returns:
        The matching URL list if found, otherwise None.
    """

    found_matching_url_list = False
    print_check(f"Checking if rule '{rule.name.split('/')[-1]}' references a URL list")

    try:
        for url_list in url_lists:
            if url_list.name in rule.session_matcher:
                print_success(
                    f"Rule references URL list '{url_list.name.split('/')[-1]}'."
                )
                found_matching_url_list = True
                return url_list

        if not found_matching_url_list:
            print_fail(f"The security policy rule does not reference any URL lists.")
        return None
    except Exception as e:
        print_fail(
            f"An error occurred when checking security policy rule for URL list match: {e}"
        )
        raise


def check_url_match_url_list(url, url_list):
    """
    Checks if the given URL matches any of the patterns in the provided URL list.

    Args:
        url: The URL to check.
        url_list: The URL list containing patterns to match against.

    Returns:
        True if a match is found, False otherwise.
    """

    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        # path in urlparse includes the leading '/', so we build host + path
        # to match against patterns like 'example.com/path/*'
        path = (
            parsed_url.path.rstrip("/")
            if parsed_url.path and parsed_url.path != "/"
            else parsed_url.path
        )
        host_and_path = hostname + path if path else hostname

        for url_value in url_list.values:
            # If pattern contains '/', match against host+path. Otherwise, match against hostname only.
            target_to_match = host_and_path if "/" in url_value else hostname

            if fnmatch.fnmatch(target_to_match, url_value):
                print(
                    f"{Colors.OKGREEN}The URL {url} matches the URL list entry {url_value}.{Colors.ENDC}"
                )
                return True

        if url_list:
            print(
                f"{Colors.FAIL}The URL {url} does not match any entry in the URL list {url_list.name}.{Colors.ENDC}"
            )

        return False
    except Exception as e:
        print_fail(f"An error occurred when checking URL against URL list: {e}")
        raise
