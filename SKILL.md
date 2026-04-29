---
name: gcp-securewebproxy-troubleshoot
description: Diagnose and troubleshoot Google Cloud Secure Web Proxy (SWP) issues. Use when users report connectivity problems to a external host, policy blocking, or certificate issues with SWP.
---

# Secure Web Proxy Troubleshoot

This skill provides a structured approach to diagnosing and resolving issues with Google Cloud Secure Web Proxy (SWP).

## Core Capabilities

1.  **Connectivity Diagnostics**: Verify if the client can reach the SWP instance.
2.  **Policy Analysis**: Inspect URL lists and security policies to determine if traffic is being blocked as intended.
3.  **Compute Engine configuration**: Verify that Compute Engine instances environment variables is correctly set to use the SWP as a proxy.
4.  **Certificate Verification**: Ensure that SSL certificates for TLS inspection are correctly installed and valid.

## Workflow Decision Tree

### 1. Connectivity Issues
If the user cannot reach the proxy at all (e.g., "Connection refused" or "Timeout"):
-   **Check Gateway Status**: Verify the SWP gateway is `READY`.
-   **Check Firewall Rules**: Ensure ingress traffic is allowed from the client VPC to the SWP subnets.
-   **Check Routing**: Verify the client has a route to the SWP gateway's IP.

### 2. Traffic Blocked (403 Forbidden)
If the user can reach the proxy but gets a 403 error:
-   **Check Security Policy**: Identify which rule in the security policy is matching the request.
-   **Check URL Lists**: Verify the target URL is in the correct `UrlList` resource.
-   **Analyze Logs**: Search SWP logs for the specific `request_id` or client IP.

### 3. TLS/SSL Errors
If the user gets "Certificate untrusted" or "Handshake failed":
-   **Check TLS Inspection Policy**: Verify if TLS inspection is enabled and which certificate is being used.
-   **Verify Root CA**: Ensure the client has the SWP's Root CA installed in its trust store.

## Useful Commands

### List Gateways
```bash
gcloud network-security gateway-security-policies list --location=[LOCATION]
```

### View SWP Logs
```bash
gcloud logging read "resource.type=\"network_security.googleapis.com/Gateway\" AND jsonPayload.proxyStatus=\"DENIED\"" --limit=10
```

## Resources

### scripts/
- `swp_troubleshoot.py`: A diagnostic script to check the status of SWP resources.

### references/
- `common_issues.md`: A reference guide for common SWP error codes and their fixes.
