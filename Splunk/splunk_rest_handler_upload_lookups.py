# Simple python script using Splunk lookup-editor https://splunkbase.splunk.com/app/1724 rest endpoint to upload lookups (wiki https://lukemurphey.net/projects/splunk-lookup-editor/wiki/REST_endpoints)

# Original author: mthcht (https://github.com/mthcht/lookup-editor_scripts)
# Modified by: Becky Burwell, April 26, 2023 (https://github.com/beckyburwell/splunk_rest_upload_lookups/blob/main/splunk_rest_upload_lookups.py)
# Modified by: Asperheek, 2024

# Last modification added to automate and maintain lookups by uploading to multiple organizations -hardcoded ips- and show final status response

#########################################################################################################################
# Usage: python .\splunk_rest_handler_upload_lookups.py <lookup_file_or_directory> <splunk_app>
#
# Example: splunk_rest_upload_lookups.py /home/burwell/mylookup.csv search
#
# Troubleshoot lookup-editor errors on splunk: index=_internal (sourcetype=lookup_editor_rest_handler OR sourcetype=lookup_backups_rest_handler)
#########################################################################################################################


import json
import requests
import logging
import getpass
import pathlib
import sys
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
lookup_path = pathlib.Path(sys.argv[1])  # File or directory
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

# List to store upload status information
upload_status = []

# Function to create an upload status entry
def create_upload_status(organization, csv_file, success):
    return {
        "Organization": organization,
        "CSV_File": csv_file.name,
        "Upload_Status": "Success" if success else "Failed"
    }

# Prompt the user for credentials and map them to their organizations
credentials_input = input("Enter credentials in the format 'username,password,organization,' (e.g., user1,password1,org1,user2,password2,org2): ")

# Parse the input, split by commas
credentials_list = credentials_input.strip().split(',')

# Iterate over the list of credentials in sets of 3 (username, password, and organization)
for i in range(0, len(credentials_list), 3):
    username = credentials_list[i]
    password = credentials_list[i + 1]
    org = credentials_list[i + 2]

    # Find the IP for the given organization
    matched_org = next((entry for entry in ips_and_orgs if entry["organization"] == org), None)
    if matched_org:
        ip = matched_org["ip"]
        logging.info(f"Found IP {ip} for organization {org}. Proceeding with login...")

        # Loop through the CSV files
        for csv_file in csv_files:
            logging.info(f"Processing file: {csv_file} for {org}")

            # Read CSV contents
            lookup_content = []
            try:
                with csv_file.open(encoding="utf-8", errors="ignore") as f:
                    for row in f:
                        lookup_content.append(row.strip().split(","))
            except Exception as e:
                logging.error(f"Error reading file {csv_file}: {e}")
                upload_status.append(create_upload_status(org, csv_file, False))
                continue

            # Send the POST request to the Splunk server
            try:
                r = requests.post(
                    f"https://{ip}:{splunk_management_port}{splunk_management_service}",  # Using the IP from the dictionary
                    verify=False,
                    auth=(username, password),
                    data={
                        "output_mode": "json",
                        "namespace": splunk_app,
                        "lookup_file": csv_file.name,
                        "contents": json.dumps(lookup_content)  # Convert lookup content to JSON
                    },
                    timeout=60
                )
                if r.status_code == 200:
                    logging.info(f"[success] File '{csv_file.name}' uploaded for IP: {ip} (Organization: {org})")
                    upload_status.append(create_upload_status(org, csv_file, True))
                else:
                    logging.error(f"[failed] File '{csv_file.name}', Status: {r.status_code}, Reason: {r.reason}, URL: {r.url}")
                    upload_status.append(create_upload_status(org, csv_file, False))
            except Exception as e:
                logging.error(f"Error uploading file '{csv_file.name}' for IP: {ip} (Organization: {org}): {e}")
                upload_status.append(create_upload_status(org, csv_file, False))
    else:
        logging.error(f"No matching organization found for: {org}")
        upload_status.append(create_upload_status(org, None, False))

# Output all upload status entries
for status in upload_status:
    print(f"Organization: {status['Organization']}, CSV_File: {status['CSV_File']}, Upload_Status: {status['Upload_Status']}")
