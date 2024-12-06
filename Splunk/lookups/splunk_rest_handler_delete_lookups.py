import json
import requests
import logging
import getpass
import pathlib
import sys
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable warning for insecure requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03dZ splunk_rest_upload_lookups: %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

# Define Splunk details
splunk_management_service = "/services/data/lookup_edit/lookup_contents"  # Endpoint for the lookup-editor
splunk_management_port = "8089"

# Example dictionary with IPs and their organizations
ips_and_orgs = [
    {"ip": "192.168.1.0", "organization": "Org A"},
    {"ip": "192.168.1.1", "organization": "Org B"},
    {"ip": "192.168.1.2", "organization": "Org C"},
    {"ip": "192.168.1.3", "organization": "Org D"},
    {"ip": "192.168.1.4", "organization": "Org E"},
    {"ip": "192.168.1.5", "organization": "Org F"},
    {"ip": "192.168.1.6", "organization": "Org G"},
    {"ip": "192.168.1.7", "organization": "Org H"},
    {"ip": "192.168.1.8", "organization": "Org I"},
    {"ip": "192.168.1.9", "organization": "Org J"},
    {"ip": "192.168.1.10", "organization": "Org K"}
]

# Validate script arguments
if len(sys.argv) != 2:
    logging.critical("[!] Usage: python splunk_rest_handler_delete_lookups.py <splunk_app>")
    logging.critical("[!] Examples for <splunk_app>: 'search', 'SplunkEnterpriseSecuritySuite', 'lookup_editor'")
    sys.exit(1)

# Get input arguments
splunk_app = sys.argv[1]

delete_status = []

# Function to create delete status entry
def create_delete_status(organization, lookup_file_or_definition, delete_success, is_definition=False):
    return {
        "Organization": organization,
        "Lookup_Type": "Definition" if is_definition else "File",
        "Name": lookup_file_or_definition,
        "Delete_Status": "Success" if delete_success else "Failed",
    }

# Prompt user for credentials
credentials_input = input(
    "Enter credentials in the format 'username,password,organization,' (e.g., user1,password1,org1,user2,password2,org2): "
)
credentials_list = credentials_input.strip().split(',')

# Ask the user what type of lookup to delete
delete_type = input(
    "What do you want to delete? (Enter 'file' for lookup files, 'definition' for lookup definitions): "
).strip().lower()

if delete_type not in ["file", "definition"]:
    logging.critical("[!] Invalid input. Please enter either 'file' or 'definition'.")
    sys.exit(1)

# Ask the user for the name of the lookup to delete
lookup_name = input(f"Enter the name of the lookup {delete_type} you want to delete: ").strip()

for i in range(0, len(credentials_list), 3):
    username, password, org = credentials_list[i:i + 3]
    matched_org = next((entry for entry in ips_and_orgs if entry["organization"] == org), None)

    if not matched_org:
        logging.error(f"No matching organization found for: {org}")
        delete_status.append(create_delete_status(org, lookup_name, False, is_definition=(delete_type == "definition")))
        continue

    ip = matched_org["ip"]
    logging.info(f"Found IP {ip} for organization {org}. Proceeding with deletion...")

    try:
        # Set the URL based on whether we're deleting a file or definition
        if delete_type == "file":
            delete_url = f"https://{ip}:{splunk_management_port}/servicesNS/admin/{splunk_app}/data/lookup-table-files/{lookup_name}"
        else:  # definition
            delete_url = f"https://{ip}:{splunk_management_port}/servicesNS/admin/{splunk_app}/data/transforms/lookups/{lookup_name}"

        # Perform the DELETE request
        response = requests.delete(
            delete_url,
            auth=HTTPBasicAuth(username, password),
            verify=False,
        )

        delete_success = response.status_code == 200
        if delete_success:
            logging.info(f"[Success] {delete_type.capitalize()} '{lookup_name}' deleted successfully for {org}.")
        else:
            logging.error(
                f"[Failed] Could not delete {delete_type} '{lookup_name}' for {org}: {response.text}"
            )

        delete_status.append(create_delete_status(org, lookup_name, delete_success, is_definition=(delete_type == "definition")))

    except Exception as e:
        logging.error(f"An error occurred during deletion for {org}: {e}")
        delete_status.append(create_delete_status(org, lookup_name, False, is_definition=(delete_type == "definition")))

# Output all delete statuses
for status in delete_status:
    logging.info(f"{status}")
