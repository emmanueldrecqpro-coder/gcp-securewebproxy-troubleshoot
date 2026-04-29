import subprocess
from utils import print_success, print_fail, print_check, Colors

from google.cloud import compute_v1
from google.api_core import exceptions


def dns_resolve_hostname(project_id: str, zone: str, instance: str, hostname: str):
    """
    Attempts to resolve the given hostname from within the specified VM instance using 'dig'.

    Args:
        project_id: The Google Cloud project ID.
        zone: The zone where the VM is located.
        instance: The name of the virtual machine.
        hostname: The hostname to resolve.
    """

    print_check(f"Checking DNS resolution for hostname: {hostname}")

    try:
        command = [
            "gcloud",
            "compute",
            "ssh",
            f"--project={project_id}",
            f"--zone={zone}",
            instance,
            f"--command=dig +short {hostname}",
            "--tunnel-through-iap",
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            resolved_ip = process.stdout.strip()
            if resolved_ip:
                print_success(
                    f"Hostname '{hostname}' resolved to IP address: {resolved_ip}"
                )

            else:
                print_fail(f"Hostname '{hostname}' did not resolve to any IP address.")
        else:
            print_fail(
                f"Failed to execute dig command. It's possible the SSH connection failed."
            )
            print(f"  {Colors.WARNING}Return Code:{Colors.ENDC} {process.returncode}")
            print(f"  {Colors.WARNING}Stderr:{Colors.ENDC}\n{process.stderr}")

    except Exception as e:
        print_fail(f"An error occurred while attempting to resolve hostname: {e}")
        raise


def get_instance_details(
    project_id: str, zone: str, instance_name: str
) -> compute_v1.Instance:
    """
    Retrieves the full details of a VM instance.

    Args:
        project_id: The Google Cloud project ID.
        zone: The zone where the VM is located.
        instance_name: The name of the virtual machine.

    Returns:
        A compute_v1.Instance object or None if not found or an error occurs.
    """
    try:
        client = compute_v1.InstancesClient()
        return client.get(project=project_id, zone=zone, instance=instance_name)
    except exceptions.NotFound:
        print_fail(
            f"Instance '{instance_name}' not found in project '{project_id}' zone '{zone}'.",
            fatal=True,
        )
        raise
    except Exception as e:
        print_fail(
            f"An unexpected error occurred while getting instance details: {e}",
            fatal=True,
        )
        raise


def get_subnet_cidr(
    instance_network_interfaces, project_id: str, region: str
) -> str | None:
    """
    Retrieves the CIDR range of the subnet associated with the instance's primary network interface.

    Args:
        instance_network_interfaces: The list of network interfaces from the instance details.
        project_id: The Google Cloud project ID.
        region: The region where the subnet is located.

    Returns:
        The CIDR range of the subnet or None if not found.
    """

    # Create a client
    client = compute_v1.SubnetworksClient()

    # Make the request
    try:

        for network_interface in instance_network_interfaces:
            if network_interface.name == "nic0":

                # Initialize request argument(s)
                request = compute_v1.GetSubnetworkRequest(
                    project=project_id,
                    region=region,
                    subnetwork=network_interface.subnetwork.split("/")[-1],
                )

                return client.get(request=request).ip_cidr_range

    except exceptions.NotFound:
        print_fail(
            "Subnetwork not found for the instance's primary network interface.",
            fatal=True,
        )
        raise
    except Exception as e:
        print_fail(
            f"An unexpected error occurred while getting subnetwork: {e}", fatal=True
        )
        raise


def get_instance_proxy_environment_variables(
    project_id: str, zone: str, instance: str
) -> dict | None:
    """
    Retrieves the proxy-related environment variables from the specified VM instance.

    Args:
        project_id: The Google Cloud project ID.
        zone: The zone where the VM is located.
        instance: The name of the virtual machine.

    Returns:
        A dictionary of proxy-related environment variables or None if not found.
    """

    try:

        command = [
            "gcloud",
            "compute",
            "ssh",
            f"--project={project_id}",
            f"--zone={zone}",
            instance,
            "--command=printenv | grep -i -e http_proxy -e https_proxy -e no_proxy",
            "--tunnel-through-iap",
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode == 0:
            env_vars = {}
            for line in process.stdout.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
            return env_vars

        return None

    except Exception as e:
        print_fail(
            f"An error occurred while retrieving instance environment variables: {e}"
        )
        raise


def check_instance_proxy_environment_variables(swp_hostname, env_vars):
    """
    Checks if the proxy environment variables contain the SWP hostname.

    Args:
        swp_hostname: The hostname of the Secure Web Proxy.
        env_vars: A dictionary of environment variables to check.

    Returns:
        None
    """

    print_check("Checking for proxy environment variables on the instance")

    try:
        if not env_vars:
            print(
                f"  {Colors.WARNING}⚠ WARNING:{Colors.ENDC} No proxy environment variables (http_proxy, https_proxy) found."
            )
            return

        for key, value in env_vars.items():
            if "http_proxy" in key.lower() or "https_proxy" in key.lower():
                if swp_hostname in value:
                    print_success(
                        f"Variable '{key}' is set to '{value}' and contains the SWP hostname."
                    )
                else:
                    print_fail(
                        f"Variable '{key}' is set to '{value}' but does NOT contain the SWP hostname '{swp_hostname}'."
                    )
            if "no_proxy" in key.lower():
                print_success(
                    f"Variable '{key}' is set to: '{value if value else '(empty)'}'"
                )
    except Exception as e:
        print_fail(
            f"An error occurred while checking instance proxy environment variables: {e}"
        )
        raise


def attempt_curl_request(url: str, project_id: str, zone: str, instance: str) -> None:
    """
    Run a curl request from the VM instance to the specified URL and check the HTTP response code.

    Args:
        url: The URL to curl.
        project_id: The Google Cloud project ID.
        zone: The zone where the VM is located.
        instance: The name of the virtual machine.

    Returns:
        None
    """

    print_check(f"Attempting to curl '{url}' from inside the VM '{instance}'")

    try:

        command = [
            "gcloud",
            "compute",
            "ssh",
            f"--project={project_id}",
            f"--zone={zone}",
            instance,
            f'--command=curl -sS -L --fail -o /dev/null -w "%{{http_code}}" {url}',
            "--tunnel-through-iap",
        ]

        # Using subprocess to capture stdout and stderr
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # Do not raise exception on non-zero exit code
        )

        http_code = process.stdout.strip()

        if process.returncode == 0 and http_code == "200":
            print_success(f"Request to '{url}' was successful (HTTP 200 OK).")
        elif http_code:
            print_fail(f"Request failed with HTTP status code: {http_code}.")
            print(f"  {Colors.WARNING}Stderr:{Colors.ENDC}\n{process.stderr}")
        else:
            print_fail(
                f"Failed to execute curl command. It's possible the SSH connection failed."
            )
            print(f"  {Colors.WARNING}Return Code:{Colors.ENDC} {process.returncode}")
            print(f"  {Colors.WARNING}Stderr:{Colors.ENDC}\n{process.stderr}")
            return

    except Exception as e:
        print_fail(f"An error occurred while attempting to curl from the instance: {e}")
        raise
