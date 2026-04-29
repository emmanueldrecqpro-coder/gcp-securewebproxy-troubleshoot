# Secure Web Proxy Troubleshoot Skill

<div style="display: flex; align-items: center;">
  <img src="references/swp_icon.png" alt="Secure Web Proxy" width="150" style="margin-right: 20px;">
</div>

<br>

## Overview

This skill helps diagnose proxy access issues for a Compute Engine instance on Google Cloud Platform (GCP) that uses [Secure Web Proxy](https://cloud.google.com/secure-web-proxy/docs/overview) (SWP). It runs a series of automated checks to identify common problems related to VM configuration, network connectivity, and SWP policies.

### Core Capabilities

*   **Connectivity Diagnostics**: Verifies if the client VM can resolve and reach the SWP gateway.
*   **Configuration Validation**: Checks instance-level settings like proxy environment variables.
*   **Policy Analysis**: Inspects SWP security policies and URL lists to determine if traffic is being handled as expected.
*   **Live Traffic Test**: Attempts a real connection from the VM to a target URL to confirm the end-to-end workflow.

## Prerequisites

*   **Google Cloud SDK**: Version 551.0.0 or later.
*   **API Access**: The `cloudaicompanion.googleapis.com` API must be enabled in your Google Cloud project.
*   **Authentication**: The script requires two forms of authentication to function correctly.
*   **IAM roles**: To run the script you need several IAM permissions. We recommend using these IAM roles
    - **Compute Engine Viewer** (roles/compute.viewer): This role is essential for retrieving details about the VM instance and its associated network configurations, such as the subnetwork.
    - **IAP-Secured Tunnel User** (roles/iap.tunnelResourceAccessor): The scripts use gcloud compute ssh with IAP tunneling to connect to the VM for live checks. This role grants the necessary permissions to establish that connection through the Identity-Aware Proxy.
    - **Network Services Viewer** (roles/networkservices.viewer): Required to get information about the Secure Web Proxy gateways.
    - **Network Security Viewer** (roles/networksecurity.viewer): This role allows the script to inspect Gateway Security Policies, their rules, and any associated URL lists.
    - **Certificate Manager Viewer** (roles/certificatemanager.viewer): Needed to retrieve details about the SSL certificates used by the SWP gateway for hostname validation.

1.  **Application Default Credentials (ADC)**: Used by the Python client libraries to make Google Cloud API calls (e.g., to get instance details and SWP policies).

    ```bash
    gcloud auth application-default login
    ```

2.  **gcloud CLI User Authentication**: Used to execute `gcloud compute ssh` commands, which connect to the VM to perform live checks like DNS resolution and curl tests.

    ```bash
    gcloud auth login
    ```

3.  **Set Quota Project**: Ensure you have a quota project set for your application default credentials. Replace `<PROJECT_ID>` with the project that will handle billing and API quotas.

    ```bash
    gcloud auth application-default set-quota-project <PROJECT_ID>
    ```

## Usage with Gemini CLI

This skill can be invoked through the Gemini CLI.

1.  **Launch gemini cli**
    ```bash
    gemini
    ```
2.  **Install and Enable the Skill**

    ```bash
    gemini skills install <URL>
    gemini skills enable securewebproxy-troubleshoot
    ```

3.  **Invoke the Skill**

    Start a conversation with a prompt related to a connectivity issue.

    > **User**: I can't connect to https://example.com/ from my VM.

    Gemini will recognize the intent and ask for permission to use the `securewebproxy-troubleshoot` skill. Once you provide the necessary parameters (project ID, instance name, zone, and URL), it will execute the script.

## Usage

You can run the troubleshooter as a standalone Python script.

### Standalone Script Execution

To run the troubleshooting script directly, execute it with the required arguments for your VM:

```bash
python3 scripts/swp_troubleshoot.py --project_id <PROJECT_ID> --instance_name <INSTANCE_NAME> --instance_zone <ZONE> --url <URL>
```

## How It Works

The script performs the following automated checks in order:

### 1. Compute Engine Instance Checks

The script first validates the client VM's configuration to ensure it is set up correctly to use the proxy.

1.  **DNS Resolution**: Checks that the VM can successfully resolve the SWP gateway's hostname.
2.  **Proxy Environment Variables**: Verifies that `http_proxy` and `https_proxy` environment variables are correctly set on the instance.
3.  **Live Curl Request**: Runs a `curl` command from within the VM to the target URL to test the end-to-end connection and check the HTTP response.

### 2. Secure Web Proxy (SWP) Checks

After validating the instance, the script inspects the SWP configuration.

1.  **Gateway Discovery**: Finds the active SWP gateway associated with the provided proxy hostname.
2.  **Security Policy Rules**: Identifies the security policy rule that applies to the source VM's subnet CIDR.
3.  **URL List Matching**: If the policy rule uses a URL list, it checks if the list is correctly referenced.
4.  **Target URL Validation**: Checks if the target URL matches an entry in the identified URL list.

Based on the results, the script prints diagnostic information to help you pinpoint the cause of the issue.
