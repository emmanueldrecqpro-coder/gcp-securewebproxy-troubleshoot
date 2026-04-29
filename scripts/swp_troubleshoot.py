import argparse
import traceback

from gateway import (
    check_security_policy_rule_match_url_list,
    check_security_policy_rules_for_subnet,
    check_url_match_url_list,
    get_gateway,
    get_gateway_based_on_hostname,
    list_gateway_security_policy_rules,
    list_url_lists,
)
from instance import (
    attempt_curl_request,
    check_instance_proxy_environment_variables,
    dns_resolve_hostname,
    get_instance_details,
    get_instance_proxy_environment_variables,
    get_subnet_cidr,
)
from utils import (
    print_fail,
    print_step,
    print_success,
    print_check,
    print_header,
    Colors,
)


def main():

    parser = argparse.ArgumentParser(description="Troubleshoot Secure Web Proxy.")

    parser.add_argument(
        "--project_id",
        required=True,
        help="Customer project ID.",
    )
    parser.add_argument(
        "--instance_name",
        required=True,
        help="Customer instance name.",
    )
    parser.add_argument(
        "--instance_zone",
        required=True,
        help="Customer instance zone.",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="The URL to troubleshoot.",
    )
    parser.add_argument(
        "--swp_project_id",
        required=True,
        help="Secure Web Proxy project ID.",
    )
    parser.add_argument(
        "--swp_location",
        required=True,
        help="Secure Web Proxy location.",
    )
    parser.add_argument(
        "--swp_hostname",
        required=True,
        help="The hostname of the Secure Web Proxy gateway.",
    )
    args = parser.parse_args()

    try:

        print(f"{Colors.BOLD}Starting Secure Web Proxy troubleshooting...{Colors.ENDC}")

        ##########################################
        # Check instance configurations and connectivity
        ##########################################

        print_step("Instance Check")

        # Get client instance configuration
        print_header("Get Client Instance Configuration")

        # Get instance details
        print_check(f"Getting details for instance '{args.instance_name}'")
        instance_details = get_instance_details(
            args.project_id, args.instance_zone, args.instance_name
        )
        print_success(f"Instance found.")

        # Get region from instance zone
        region = (
            args.instance_zone.split("-")[0] + "-" + args.instance_zone.split("-")[1]
        )

        print_check("Getting instance subnet CIDR")
        subnet_cidr = get_subnet_cidr(
            instance_details.network_interfaces, args.project_id, region
        )
        print_success(f"Instance subnet CIDR is '{subnet_cidr}'.")

        # Check DNS resolution from the instance to the gateway hostname
        print_header("DNS Resolution Check")
        dns_resolve_hostname(
            args.project_id, args.instance_zone, args.instance_name, args.swp_hostname
        )

        # Check instance proxy environment variables
        print_header("Instance Proxy Settings")
        env_vars = get_instance_proxy_environment_variables(
            args.project_id, args.instance_zone, args.instance_name
        )
        check_instance_proxy_environment_variables(args.swp_hostname, env_vars)

        # Test request in VM
        print_header("Live Traffic Test")
        attempt_curl_request(
            args.url, args.project_id, args.instance_zone, args.instance_name
        )

        ##########################################
        # Check gateway global configurations
        ##########################################
        print_step("Checking Secure Web Proxy Configuration")
        print_header("Secure Web Proxy Configuration")

        gateway = get_gateway_based_on_hostname(
            args.swp_project_id, args.swp_location, args.swp_hostname
        )

        gateway_details = get_gateway(
            args.swp_project_id, args.swp_location, gateway.name.split("/")[-1]
        )

        gateway_security_policy_rules = list_gateway_security_policy_rules(
            security_policy_path=gateway_details.gateway_security_policy
        )

        rule = check_security_policy_rules_for_subnet(
            gateway_security_policy_rules, subnet_cidr
        )

        if rule:
            # Get url lists and check if any of them are used in the security policy rules
            url_lists = list_url_lists(args.swp_project_id, args.swp_location)
            url_list = check_security_policy_rule_match_url_list(rule, url_lists)

            if url_list:
                check_url_match_url_list(args.url, url_list)

        print(f"\n{Colors.BOLD}Troubleshooting finished.{Colors.ENDC}")

    except Exception as e:
        print_fail(
            f"An unexpected error occurred during troubleshooting: {e}", fatal=True
        )
        print_fail(traceback.format_exc())


if __name__ == "__main__":
    main()
