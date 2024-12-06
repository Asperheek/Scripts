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
if len(sys.argv) != 3:
    logging.critical("[!] Usage: python .\splunk_rest_handler_upload_lookups.py <lookup_file_or_directory> <splunk_app>")
    logging.critical("[!] Examples for <splunk_app>: 'search', 'SplunkEnterpriseSecuritySuite', 'lookup_editor'")
    sys.exit(1)

# Get input arguments
lookup_path = pathlib.Path(sys.argv[1])
splunk_app = sys.argv[2]

# Check if the provided path is a file or directory
if lookup_path.is_file():
    csv_files = [lookup_path]
elif lookup_path.is_dir():
    csv_files = list(lookup_path.glob("*.csv"))
    if not csv_files:
        logging.error(f"No CSV files found in directory: {lookup_path}")
        sys.exit(1)
else:
    logging.error(f"Invalid path: {lookup_path}")
    sys.exit(1)

upload_status = []

# Function to create an upload status entry
def create_upload_status(organization, csv_file, upload_success, definition_success=None):
    return {
        "Organization": organization,
        "CSV_File": csv_file.name if csv_file else "N/A",
        "Upload_Status": "Success" if upload_success else "Failed",
        "Lookup_Definition_Status": "Success" if definition_success else ("N/A" if definition_success is None else "Failed")
    }

# Prompt user for credentials
credentials_input = input(
    "Enter credentials in the format 'username,password,organization,' (e.g., user1,password1,org1,user2,password2,org2): "
)
credentials_list = credentials_input.strip().split(',')

# Ask user once about lookup definition creation
create_lookups = input("Do you want to create lookup definitions for all files? (yes/no): ").strip().lower()
create_lookups_choice = create_lookups == "yes"

lookup_name = None
match_type = None
case_sensitive_match = None

if create_lookups_choice:
    lookup_name = input("Enter the name for the lookup definition (leave blank to use the CSV filename): ").strip()
    match_type = input("Enter match type (e.g., WILDCARD(keyword)) or press Enter to use default: ").strip()
    case_sensitive = input("Is case-sensitive match required? (yes/no): ").strip().lower()
    case_sensitive_match = "1" if case_sensitive == "yes" else "0"

for i in range(0, len(credentials_list), 3):
    username, password, org = credentials_list[i:i + 3]
    matched_org = next((entry for entry in ips_and_orgs if entry["organization"] == org), None)

    if not matched_org:
        logging.error(f"No matching organization found for: {org}")
        upload_status.append(create_upload_status(org, None, False))
        continue

    ip = matched_org["ip"]
    logging.info(f"Found IP {ip} for organization {org}. Proceeding with login...")

    for csv_file in csv_files:
        logging.info(f"Processing file: {csv_file} for {org}")
        try:
            with csv_file.open(encoding="utf-8", errors="ignore") as f:
                lookup_content = [row.strip().split(",") for row in f]

            r = requests.post(
                f"https://{ip}:{splunk_management_port}{splunk_management_service}",
                verify=False,
                auth=(username, password),
                data={
                    "output_mode": "json",
                    "namespace": splunk_app,
                    "lookup_file": csv_file.name,
                    "contents": json.dumps(lookup_content)
                },
                timeout=60
            )
            upload_success = r.status_code == 200
            logging.info(
                f"[{'success' if upload_success else 'failed'}] File '{csv_file.name}' uploaded for {org} with IP {ip}"
            )
        except Exception as e:
            logging.error(f"Error uploading file '{csv_file.name}' for {org}: {e}")
            upload_success = False

        definition_success = None
        if create_lookups_choice:
            current_lookup_name = lookup_name or csv_file.stem

            url_create_lookup = f"https://{ip}:{splunk_management_port}/servicesNS/admin/{splunk_app}/data/transforms/lookups/"
            data_create = {
                "name": current_lookup_name,
                "filename": csv_file.name,
                "match_type": match_type,
                "case_sensitive_match": case_sensitive_match,
            }

            try:
                response_create = requests.post(
                    url_create_lookup,
                    data=data_create,
                    auth=HTTPBasicAuth(username, password),
                    verify=False
                )
                definition_success = response_create.status_code == 201
                if definition_success:
                    logging.info(f"Lookup definition '{current_lookup_name}' created successfully for {org}.")
                else:
                    logging.error(f"Failed to create lookup definition '{current_lookup_name}' for {org}.")
            except Exception as e:
                logging.error(f"An error occurred during lookup definition creation: {e}")

            # Modify permissions for lookup definition
            if definition_success:
                url_modify_perms = f"{url_create_lookup}{current_lookup_name}/acl"
                data_modify_perms = {"sharing": "global", "owner": "nobody"}
                try:
                    response_modify = requests.post(
                        url_modify_perms,
                        data=data_modify_perms,
                        auth=HTTPBasicAuth(username, password),
                        verify=False
                    )
                    if response_modify.status_code == 200:
                        logging.info(f"Permissions for '{current_lookup_name}' set to global.")
                    else:
                        logging.error(f"Failed to update permissions for '{current_lookup_name}'.")
                except Exception as e:
                    logging.error(f"Error updating permissions for '{current_lookup_name}': {e}")

        upload_status.append(create_upload_status(org, csv_file, upload_success, definition_success))

# Output all upload statuses
for status in upload_status:
    logging.info(f"{status}")
