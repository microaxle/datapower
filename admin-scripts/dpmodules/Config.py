import requests
from datetime import datetime
from termcolor import colored
import json
import sys
from dpmodules import Status as STATS
from dpmodules import Config as CONFIG
from dpmodules import ini as INI
from tqdm import tqdm
import time

# @@@@@@@@@@@@@@@------------- def create_checkpoint(appliance, domain): ------------- ***@@@@@@@@@@@@@@@@
# ------------------------------------------------------------------------------------------------------------------ 
def create_checkpoint(appliance, domain):
    
    # Verify given host is pingable
    STATS.ishost_valid(appliance)

    # Check the given domain is available or not
    STATS.isdomain_available(appliance, domain)
        
    # Generate checkpoint dynamic check point name 'chk-domain name-date'
    checkpoint_name = f"chk-{domain}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
    # Construct payload
    request_payload = {"SaveCheckpoint": {"ChkName": checkpoint_name}}
    
    # submit request to datapower
    response = requests.post(f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/{domain}", data=json.dumps(request_payload), auth=INI.authinfo, verify=False)
    
    # Validate response and act based on status code recived
    if response.status_code == 401:
        sys.exit("Error: Authentication Failure")

    # Once got sucess reponse, validate the response payload for expected value
    if response.status_code == 202:
        # Datapower actionqueue operations generate dynamic location in datapower for action status. capture that and analyse how operation is preforming.
        action_location = f"https://{appliance}:{INI.api_port}{response.json().get('_links').get('location').get('href')}"
        
        # Call the datapower pending action url and check the status
        action_status = requests.get(action_location, auth=INI.authinfo, verify=False)
        
        # If any error, Print the error 
        if action_status.json().get('status') == 'error':
            print(f"\n{colored('Alert:', 'red')}, {action_status.json().get('error')[0]}")
            STATS.get_checkpoint_list(appliance, domain)
           
        else:
            for i in tqdm (range (INI.checkpoint_wait_time), desc=f"Checkpointing on '{domain}'", ascii=False, ncols=75):
                time.sleep(1)
            print(f"{colored('INFO: ', 'green')}Checkpoint Creation is Completed successfully.\n")
            CONFIG.save_config(appliance, domain)
                                

# @@@@@@@@@@@@@@@------------- delete_checkpoint(appliance, domain, chkname) ------------- ***@@@@@@@@@@@@@@@@
# ----------------------------------------------------------------------------------------------------------------------
def delete_checkpoint(appliance, domain):

    # Check given host is valid
    STATS.ishost_valid(appliance)
    
    # Check given domain is valid
    STATS.isdomain_available(appliance, domain)
    
    # Help user by displaying existing checkpoint list. so that user can chose what to remove
    func_return = STATS.get_checkpoint_list(appliance, domain)
    if func_return:
        sys.exit(f"\n{colored('INFO: ', 'green')}No Checkpoints Available on Given {domain} domain\n")
    
    # Ask user to delete selected checkpoint
    chkname = input(f"Provide the checkpoint name from above list to delete : ")

    # Generate payload to send datapower
    request_payload = { "RemoveCheckpoint": { "ChkName": chkname } }
    
    # Call datapower to delete checkpoint
    response = requests.post(f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/{domain}", data=json.dumps(request_payload), auth=INI.authinfo, verify=False)
    
    # Act based on response code. if it is 400 then throw an error
    if response.status_code == 400 and 'error' in response.json():
        print(f"\n{colored('ERROR: ', 'red')}", {response.json().get("error")[1]})
    
    # If response is success, print succes smessage
    if response.status_code == 200 and 'RemoveCheckpoint' in response.json():
        print(f"\n{colored('INFO: ', 'green')} Configuration Checkpoint \'{chkname}\' is removed")
            

# @@@@@@@@@@@@@@@------------- set_prob() ------------- ***@@@@@@@@@@@@@@@@
# set_prob() function takes 5 arguments 
def set_prob(appliance, domain, object_name, action):
    
    # check the appliance connection
    STATS.ishost_valid(appliance)

    # Once connection is successfull in previous step, check the given domain is available or not.
    STATS.isdomain_available(appliance, domain)       

    # Get the object info
    object_info = STATS.get_object_info(appliance, domain, object_name)
    
    
    request_payload = {"DebugMode": action}
    operation_url = ""

    # Dynamically constructing operational url based on Object class
    if object_name == 'all':
        for item in object_info:
            if item["Class"] == "WSGateway" or item["Class"] == "MultiProtocolGateway":
                operation_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain}/{item['Class']}/{item['Name']}/DebugMode"
                response = requests.put(operation_url, data=json.dumps(request_payload), auth=INI.authinfo, verify=False)
                if response.status_code == 401:
                    sys.exit("Error: Authentication Failure")
                if response.status_code == 200 and response.json().get('DebugMode') == 'Property was updated.':
                    print(f"{colored('INFO: ', 'green')}Prob Operation is Successfull on {item['Name']}")
    
    
    else:
        for item in object_info:
            if (item["Class"] == "WSGateway" and item["Name"] == object_name) or (item["Class"] == "MultiProtocolGateway" and item["Name"] == object_name):
                operation_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain}/{item['Class']}/{object_name}/DebugMode"
    
                # call datapower for enabling/disabling prob on given service
                response = requests.put(operation_url, data=json.dumps(request_payload), auth=INI.authinfo, verify=False)
    
                # check response code and act upon
                if response.status_code == 401:
                    sys.exit("Error: Authentication Failure")
        
                if response.status_code == 404:
                    sys.exit(f"The Resource '{object_name}' not found on {domain}")

                # Once got sucess reponse, validate the response payload for expected value
                if response.status_code == 200 and response.json().get('DebugMode') == 'Property was updated.':
                    print(f"{colored('INFO: ', 'green')}Prob Operation is Successfull on {object_name}")

# @@@@@@@@@@@@@@@------------- restart_service(appliance, domain, object) ------------- ***@@@@@@@@@@@@@@@@
  
# @@@@@@@@@@@@@@@------------- save_config(appliance, domain) ------------- ***@@@@@@@@@@@@@@@@
def save_config(appliance, domain):

    # Check the appliance is pingable
    STATS.ishost_valid(appliance)

    # Check if the domain is available on given appliance
    STATS.isdomain_available(appliance, domain)

    # Construct URL and Payload
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/{domain}"
    request_data = {"SaveConfig": "0"}
    
    # Call datapower with Payload
    response = requests.post(operation_url, data=json.dumps(request_data), auth=INI.authinfo, verify=False)
      
    # If authentication failure, it throws authentication error
    if response.status_code == 401:
        print(f"{colored('ERROR: ', 'red')}Authentication Failure")

    # Once got sucess reponse, validate the response payload for expected value
    if response.status_code == 200 and response.json().get('SaveConfig') == 'Operation completed.':
        print(f"{colored('INFO: ', 'green')}SaveConfig is Successfull on {domain} domain\n")
       
    

def main():
    pass
if __name__=="__main__":
    main()



