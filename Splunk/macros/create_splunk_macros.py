import json
import requests
import logging
import getpass
import pathlib
import sys
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


if len(sys.argv) != 2:
    logging.critical("[!] Usage: python create_splunk_macros.py <splunk_app>")
    sys.exit(1)


splunk_app = sys.argv[1]


credentials_input = input(
    "Enter credentials in the format 'username,password,organization,' (e.g., user1,password1,org1,user2,password2,org2): "
)
credentials_list = credentials_input.strip().split(',')


ips_and_orgs = [
    {"ip": "xxxxx.splunkcloud.com", "organization": "test_cloud"},
    {"ip": "192.168.100.1", "organization": "test_ip"}
]


macro_name = input("Enter the macro name to create: ").strip()
macro_definition = input("Enter the macro definition (e.g., 'index=* sourcetype=*'): ").strip()
macro_description = input("Enter a description for the macro (optional): ").strip()


upload_status = []


for i in range(0, len(credentials_list), 3):
    username, password, org = credentials_list[i:i + 3]
    matched_org = next((entry for entry in ips_and_orgs if entry["organization"] == org), None)

    if not matched_org:
        logging.error(f"No matching organization found for: {org}")
        upload_status.append({"Organization": org, "Macro_Name": macro_name, "Status": "Failed - Org not found"})
        continue

    ip = matched_org["ip"]
    logging.info(f"Processing Splunk instance for organization: {org} at {ip}")

    
    url_create_macro = f"https://{ip}:8089/servicesNS/nobody/{splunk_app}/configs/conf-macros"

    
    data = {
        "name": macro_name,
        "definition": macro_definition,
        "description": macro_description,
    }

    
    try:
        response = requests.post(
            url_create_macro,
            auth=HTTPBasicAuth(username, password),
            verify=False,
            data=data
        )
        definition_success = response.status_code in [200, 201]
        if definition_success:
            logging.info(f"Successfully created macro '{macro_name}' for organization '{org}'.")
            upload_status.append({"Organization": org, "Macro_Name": macro_name, "Status": "Success"})
        else:
            logging.error(f"Failed to create macro '{macro_name}' for {org}. Response: {response.text}")
            upload_status.append({"Organization": org, "Macro_Name": macro_name, "Status": "Failed"})
            continue
    except Exception as e:
        logging.error(f"Error creating macro '{macro_name}' for organization '{org}': {e}")
        upload_status.append({"Organization": org, "Macro_Name": macro_name, "Status": "Error"})
        continue

    
    if definition_success:
        url_modify_perms = f"https://{ip}:8089/servicesNS/nobody/{splunk_app}/configs/conf-macros/{macro_name}/acl"
        data_modify_perms = {"sharing": "global", "owner": "nobody"}

        try:
            response_modify = requests.post(
                url_modify_perms,
                auth=HTTPBasicAuth(username, password),
                verify=False,
                data=data_modify_perms
            )
            if response_modify.status_code in [200, 201]:
                logging.info(f"Permissions for '{macro_name}' set to global for organization '{org}'.")
            else:
                logging.error(f"Failed to update permissions for '{macro_name}' for organization '{org}'. Response: {response_modify.text}")
        except Exception as e:
            logging.error(f"Error updating permissions for '{macro_name}' for organization '{org}': {e}")


for status in upload_status:
    logging.info(status)
