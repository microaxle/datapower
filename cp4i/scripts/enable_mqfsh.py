"""
Author: Annu Singh
Date: 2024-Aug-23
Description: Generate Datapower MQFSH status report.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json, base64, requests, os, argparse
from datetime import datetime
from time import sleep
from jproperties import Properties
from termcolor import colored

configs = Properties()
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication.
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Get the directory containing the current script.
script_location = os.path.dirname(os.path.realpath(__file__))

# Create log location if not present.
if not os.path.exists(f"{script_location}/logs"):
    os.makedirs(f"{script_location}/logs")

# Once find the script location, load properties file from the config location. this helps user to keep these scripts home folder any where in the system.
with open(f"{script_location}/dp-config.properties", 'rb') as config_file:
    configs.load(config_file)


# Load all the required custom values from the properties file.
authinfo = (configs.get("user").data, base64.b64decode(configs.get("cred").data).decode("utf-8"))
#api_port = int(configs.get("api_port").data)
#api_port 5554 is not required for CP4I because of the Openshift route which runs on default TLS port.

def check_standby_status(appliance):

    operation_url = f"https://{appliance}/mgmt/status/default/StandbyStatus2"
    response = requests.get(operation_url, auth=authinfo, verify=False)
    # Some times if appliance is not the part of High availability enabled we may get "No status retrieved" message.
    # So we need to handle that as active box
    if response.json().get('result') == 'No status retrieved.':
        return 'active'
    else:
        result = response.json().get('StandbyStatus2').get('State')
        return result

# This is the function which helps to check the give user and its credentials supplied through properties file.
def check_user(appliance):
    # Simply call a active users api where authentication is required and validate the response.
    operation_url = f"https://{appliance}/mgmt/status/default/ActiveUsers"
    response = requests.get(operation_url, auth=authinfo, verify=False)
    result = response.json()

    # if any error in connection, capture the result and print to users screen. else pass the control to next level.
    if 'error' in result:
        print(f"{colored('ERROR: ', 'red')} Provided Credentials are not valid\n")
        sys.exit()
    else:
        pass

# This function helps to validate the supplied appliance.
def ishost_valid(appliance):
    # It calls base resource path of the Datapower REST API and validate the response.
    # If successful connection, then it passes the control to next level, else it prints the exception and close the program.
    try:
        requests.get(f"https://{appliance}/mgmt/", verify=False)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def get_domain_names(appliance):

    # Once the appliance is valid and pingable, call the dp REST SERVICE with below resource
    response = requests.get(f"https://{appliance}/mgmt/domains/config/", auth=(authinfo), verify=False)
    domains_object = response.json().get('domain')

    domain_names = []
    if type(domains_object) is dict:
        domain_names.append(domains_object['name'])

    elif type(domains_object) is list:
        for item in response.json().get('domain'):
            domain_names.append(item['name'])

    return domain_names

def isdomain_available(appliance, domain):
    domain_list = get_domain_names(appliance)
    if domain in domain_list:
        pass
    else:
        print(f"{colored('ERROR: ', 'red')}{domain} domain is not available/accesible\n")
        sys.exit()

def mqfsh_enable(appliance, domain):

    domain_list = []
    if domain != "all":
        isdomain_available(appliance, domain)
        domain_list.append(domain)

    if domain == "all":
        domain_list = get_domain_names(appliance)

    mqfsh_enable_request = {"mAdminState": "enabled"}
    save_request = { "SaveConfig" : "0" }

    for domain in domain_list:
        obj_response = requests.get(f"https://{appliance}/mgmt/status/{domain}/ObjectStatus", auth=(authinfo), verify=False)
        list_objects = obj_response.json().get("ObjectStatus")

        mqfsh_list = []
        for item in list_objects:
           if item['Class'] == 'MQv9PlusSourceProtocolHandler' and  item['AdminState'] != 'enabled':
              mqfsh_list.append(item['Name'])

        if not mqfsh_list:
            continue

        for mqfsh in mqfsh_list:
            config_response = requests.put(f"https://{appliance}/mgmt/config/{domain}/MQv9PlusSourceProtocolHandler/{mqfsh}/mAdminState", data=json.dumps(mqfsh_enable_request), auth=(authinfo), verify=False)
            fsh_status_uri = config_response.json().get('_links').get('self')['href']

            status_response = requests.get(f"https://{appliance}{fsh_status_uri}", auth=(authinfo), verify=False)

            with open(f"{script_location}/logs/mqfsh_enabled.log", 'a') as f:
                print(f"{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}: {appliance}, {domain}, {mqfsh} - {status_response.json()['mAdminState']}", file=f)


        requests.post(f"https://{appliance}/mgmt/actionqueue/{domain}", data=json.dumps(save_request), auth=(authinfo), verify=False)
        with open(f"{script_location}/logs/mqfsh_enabled.log", 'a') as f:
                print(f"{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}: {appliance}, {domain}, changes are saved", file=f)

def mqfsh_disable(appliance, domain):
    domain_list = []
    if domain != "all":
        isdomain_available(appliance, domain)
        domain_list.append(domain)

    if domain == "all":
        domain_list = get_domain_names(appliance)

    mqfsh_disable_request = {"mAdminState": "disabled"}
    save_request = { "SaveConfig" : "0" }

    for domain in domain_list:
        obj_response = requests.get(f"https://{appliance}/mgmt/status/{domain}/ObjectStatus", auth=(authinfo), verify=False)
        list_objects = obj_response.json().get("ObjectStatus")

        mqfsh_list = []
        for item in list_objects:
           if item['Class'] == 'MQv9PlusSourceProtocolHandler' and  item['AdminState'] != 'disabled':
              mqfsh_list.append(item['Name'])

        if not mqfsh_list:
            continue

        for mqfsh in mqfsh_list:
            config_response = requests.put(f"https://{appliance}/mgmt/config/{domain}/MQv9PlusSourceProtocolHandler/{mqfsh}/mAdminState", data=json.dumps(mqfsh_disable_request), auth=(authinfo), verify=False)
            fsh_status_uri = config_response.json().get('_links').get('self')['href']

            status_response = requests.get(f"https://{appliance}{fsh_status_uri}", auth=(authinfo), verify=False)

            with open(f"{script_location}/logs/mqfsh_disbaled.log", 'a') as f:
                print(f"{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}: {appliance}, {domain}, {mqfsh} - {status_response.json()['mAdminState']}", file=f)


        requests.post(f"https://{appliance}/mgmt/actionqueue/{domain}", data=json.dumps(save_request), auth=(authinfo), verify=False)
        with open(f"{script_location}/logs/mqfsh_disbaled.log", 'a') as f:
                print(f"{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}: {appliance}, {domain}, changes are saved", file=f)



def main():
    parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True)
    parser.add_argument("-d", "--domain", help="Datapower Application Domain or 'all' - It is Required Argument", required=True)

    # parse and store all the user arguments into 'args' variable
    args = parser.parse_args()

    check_user(args.appliance)
    ishost_valid(args.appliance)
    ha_status = check_standby_status(args.appliance)
    if ha_status == 'active':
        mqfsh_enable(args.appliance, args.domain)
    elif ha_status == 'standby':
        mqfsh_disable(args.appliance, args.domain)

if __name__ == "__main__":
    main()


