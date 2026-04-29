from google.cloud import certificate_manager_v1
from google.api_core import gapic_v1

from utils import print_fail


def get_certificate(project_id, location, certificate_name):
    """
    Retrieves a certificate by name using the Certificate Manager API.

    Args:
        project_id (str): The ID of the Google Cloud project.
        location (str): The location of the certificate.
        certificate_name (str): The name of the certificate to retrieve.

    Returns:
        The certificate object or None if an error occurred.
    """
    # Create a client
    client = certificate_manager_v1.CertificateManagerClient()

    # Initialize request argument(s)
    request = certificate_manager_v1.GetCertificateRequest(
        name=f"projects/{project_id}/locations/{location}/certificates/{certificate_name}",
    )

    try:
        # Make the request
        return client.get_certificate(
            request=request, retry=gapic_v1.method.DEFAULT, timeout=10.0
        )
    except Exception as e:
        print_fail(f"An error occurred when getting certificate: {e}")
        raise
