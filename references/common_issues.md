# Common SWP Issues and Fixes

## 403 Forbidden
-   **Cause**: The security policy is missing a rule to allow the traffic, or the rule is after a more specific deny rule.
-   **Fix**: Check the `GatewaySecurityPolicy` rules. Ensure the `UrlList` contains the target domain and the rule is in the correct priority.

## 502 Bad Gateway
-   **Cause**: The SWP instance cannot reach the target destination. This could be due to DNS issues or egress firewall rules.
-   **Fix**: Verify the SWP subnets can resolve the target domain and have egress access (e.g., via Cloud NAT).

## Certificate Errors (TLS Interception)
-   **Cause**: The client does not trust the SWP's Root CA, or the SWP is using an expired or invalid certificate for interception.
-   **Fix**: Verify the `TlsInspectionPolicy` and ensure the client machine has the CA certificate installed in its system trust store.

## Connectivity Timeout
-   **Cause**: Firewall rules are blocking ingress traffic from the client to the SWP subnets, or the SWP subnets don't have enough capacity.
-   **Fix**: Check the VPC firewall rules and the SWP gateway status.
