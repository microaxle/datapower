from dpmodules import Status as STATS
from dpmodules import Config as CONFIG
from dpmodules import Helper as HELPER
from dpmodules import ini as INI
from termcolor import colored
from datetime import datetime
import time
import json
import requests
import os
from tqdm import tqdm
from time import sleep

def backup_domain(appliance, domain):

    STATS.ishost_valid(appliance)
    domain_list = []

    if domain != "all":
        STATS.isdomain_available(appliance, domain)
        domain_list.append(domain)
    
    if domain == "all":
        domain_list = STATS.get_domain_names(appliance)

    for item in domain_list:
        domain = item
        request_payload = {"Export": {
            "Format": "ZIP",
            "UserComment": f"Export {domain} - {datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}",
            "Persisted": "on",
            "AllFiles": "on",
            "IncludeInternalFiles": "on",
            "Domain":
                {
                "name": domain,
                "ref-objects": "on"
                },
            }
        }

        operation_url = f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/default"
        encode_file = f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/{domain}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
        decode_file = f"{INI.code_base}/{appliance}/{domain}/{domain}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.zip"
        response = requests.post(operation_url, data=json.dumps(request_payload, indent = 4), auth=INI.authinfo, verify=False)
    
        if response.status_code == 202:
        
            f_location = response.json().get('_links').get('location').get('href')
            for i in tqdm (range (INI.domain_backup_wait_time), desc=f"Taking '{domain}' Backup", ascii=False, ncols=75):
                time.sleep(1)

            get_file = requests.get(f"https://{appliance}:{INI.api_port}{f_location}", auth=INI.authinfo, verify=False)
            #print(get_file.json())

            with open(f"{encode_file}", "w") as file1:
                file1.write(get_file.json().get('result').get('file'))
                for i in tqdm (range (10), desc=f"Downloading '{domain}' Backup File", ascii=False, ncols=75):
                    time.sleep(1)
        
            cmd = (f"base64 -d {encode_file} > {decode_file}")
            os.popen(cmd)
            sleep(5)
            print(f"{colored('INFO: ', 'green')}file \'{decode_file}\' is downloaded successfully.\n")
        

def restore_domain(appliance, domain, zip_file, DryRun="off"):

    # Check given zip is existed or not
    HELPER.check_file_exists(zip_file)
    # Check the appliance is reachable
    STATS.ishost_valid(appliance)
    # Create Checkpoint ( This function checks automatically the given appliance and domain available or not)
    #CONFIG.create_checkpoint(authinfo, appliance, domain)
    # After checkpointing, take domain backup and download into datapower_code_repository
    #download_domain(authinfo, appliance, domain)

    request_payload = {
                    "Import":{
                        "InputFile":"base64-encoded BLOB",
                        "Format":"ZIP",
                        "OverwriteObjects": "on",
                        "OverwriteFiles": "on",
                        "RewriteLocalIP": "on",
                        "DryRun": DryRun
                        }
                    }
    # save base64 command in a variable.
    cmd = "base64 " + str(zip_file)

    # This line converts zip file into base64 by calling os.popen function and inserts the output into the request data dictionory.
    request_payload["Import"]["InputFile"] = os.popen(cmd).read()
    
    # Dynamically construct the url.
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/default"
    
    # Finally call and send the request data on datapower url and stores the output in a variable called response.
    response = requests.post(operation_url, data=json.dumps(request_payload, indent = 4), auth=INI.authinfo, verify=False)

    if response.status_code == 202 and response.json().get('Import').get('status') == 'Action request accepted.':
        for i in tqdm (range (INI.domain_restore_wait_time), desc=f"Deploying the zip", ascii=False, ncols=75):
                time.sleep(1)

        CONFIG.save_config(appliance, "default")
        sleep(5)
        CONFIG.save_config(appliance, domain)
        

def backup_object(appliance, domain, object_name="none", refobjects="on", reffiles="on"):

    # Check the given appliance is reachable
    STATS.ishost_valid(appliance)

    # Check the given domain is correct and available
    STATS.isdomain_available(appliance, domain)
       
    # Identify the object class ( calling function from Helper Module )
    ObjClass = HELPER.get_object_class(appliance, domain, object_name)

    # Dynamically construct the request payload
    request_payload = {"Export":
                        {
                        "Format": "ZIP",
                        "UserComment": f"Downloading {object_name} from {domain}",
                        "Object":
                        [
                            {
                            "class": ObjClass,
                            "name": object_name,
                            "ref-objects": refobjects,
                            "ref-files": reffiles,
                            },
                            
                        ]
                        }
                    }
    
    # Dynamically Construct the operation url to send the above request payload
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/{domain}"

    # This function download the object in base64 format. Hence before converting into zip, we are storing it in '.encodedfiles' location
    encode_file = f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/{object_name}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"

    # This is actual name object name which we need to convert encoded file to zip 
    decode_file = f"{INI.code_base}/{appliance}/{domain}/{object_name}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.zip"

    # Posting the request payload to datapower operational url
    response = requests.post(operation_url, data=json.dumps(request_payload, indent = 4), auth=INI.authinfo, verify=False)
    
    # Validating response status code.
    if response.status_code == 202:
        
        # Datapower gives us the url of the file or object or domain from where to download.
        f_location = response.json().get('_links').get('location').get('href')

        # When we sent reqeust for a file to Datapower, it may take bit time to preparting the encoded data of the file. Hence we are just waiting for some here.
        for i in tqdm (range (10), desc=f"Taking '{object_name}' Backup", ascii=False, ncols=75):
                time.sleep(1)

        # After the wait time, calling the location url to get the base64 data.
        get_file = requests.get(f"https://{appliance}:{INI.api_port}{f_location}", auth=INI.authinfo, verify=False)
        
        # Opening encoded file with write permission and writing the base64 data in it.
        with open(f"{encode_file}", "w") as file1:
            file1.write(get_file.json().get('result').get('file'))

            # Waiting for some to properly saving the base64 data into encodedfile.
            for i in tqdm (range (10), desc=f"Downloading '{object_name}' Backup File", ascii=False, ncols=75):
                time.sleep(1)
        
        # Preparing Linux Command and Calling os method to convert the encoded file to zip file.
        cmd = (f"base64 -d {encode_file} > {decode_file}")
        os.popen(cmd)

        # Conversion may take bit time, Hence we are waiting for some time to complete the operation properly.
        for i in tqdm (range (10), desc=f"Convert and Saving '{object_name}' Backup File", ascii=False, ncols=75):
                time.sleep(1)
                
        # Finally Printing the message
        print(f"\n{colored('INFO: ', 'green')}file \'{decode_file}\' is downloaded successfully.")


def deploy_object(appliance, domain, zip_file, OverwriteObjects="on", OverwriteFiles="on", DryRun="off"):

    # Check given zip is existed or not
    HELPER.check_file_exists(zip_file)
    # Create Checkpoint ( This function checks automatically the given appliance and domain available or not)
    #CONFIG.create_checkpoint(authinfo, appliance, domain)
    # After checkpointing, take domain backup and download into datapower_code_repository
    #download_domain(authinfo, appliance, domain)

    STATS.ishost_valid(appliance)
    STATS.isdomain_available(appliance, domain)
        

    request_payload = {
                    "Import":{
                        "InputFile":"base64-encoded BLOB",
                        "Format":"ZIP",
                        "OverwriteObjects": OverwriteObjects,
                        "OverwriteFiles": OverwriteFiles,
                        "DryRun": DryRun
                        }
                    }
    # save base64 command in a variable.
    cmd = "base64 " + str(zip_file)

    # This line converts zip file into base64 by calling os.popen function and inserts the output into the request data dictionory.
    request_payload["Import"]["InputFile"] = os.popen(cmd).read()
    
    # Dynamically construct the url.
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/actionqueue/{domain}"
    
    # Finally call and send the request data on datapower url and stores the output in a variable called response.
    response = requests.post(operation_url, data=json.dumps(request_payload, indent = 4), auth=INI.authinfo, verify=False)
        
    if response.status_code == 202 and response.json().get('Import').get('status') == 'Action request accepted.':
        for i in tqdm (range (10), desc=f"Deploying the file", ascii=False, ncols=75):
                time.sleep(1)

        CONFIG.save_config(appliance, domain)
        
def secure_backup(appliance):

    #Check the given appliance is reachable/available
    STATS.ishost_valid(appliance)

    secure_main_dir = f"{INI.code_base}/{appliance}/SecureBackups/{appliance}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    secure_enc_dir =  f"{INI.code_base}/.encodedfiles/{appliance}/SecureBackups/{appliance}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not os.path.exists(secure_main_dir):
        os.makedirs(secure_main_dir)
    if not os.path.exists(secure_enc_dir):
        os.makedirs(secure_enc_dir)


    # Construct request payload with selection of certificate and destination on the datapower to store all secure backup files.
    # We are using local:///SecureOne as filesystem
    request_payload = {
                    "SecureBackup":{
                        "cert": INI.secure_cert,
                        "destination": INI.secure_destination,
                        }
                    }

    # Check if local:///SecureOne is available or not on appliance. if not create it

    
    # Submit the request payload to appliance and collect the response with pending status url.
    response = requests.post(f'https://{appliance}:{INI.api_port}/mgmt/actionqueue/default', data=json.dumps(request_payload, indent = 4), auth=INI.authinfo, verify=False)
    
    # Once you submit, wait for some time to generate all the secure backup files on the appliance.
    # This depends on size of the appliance. tune the wait time accordingly.
    for i in tqdm (range (20), desc=f"Progressing SecureBackup Activity on {appliance}", ascii=False, ncols=75):
                time.sleep(1)

    # Once wait time is done, call the datapower with pending status url
    request_status = requests.get(f'https://{appliance}:{INI.api_port}{response.json().get("_links").get("location").get("href")}', auth=INI.authinfo, verify=False)
    
    # If request_status is 200 and payload contains status as completed then proceed for next actions. else exit with error info
    if request_status.status_code == 200 and request_status.json().get("status") == 'completed':

        # Once Secure backup request processed by Datapower, Now we need to work on to download those files one by one.
        # get the list off files available on local:///SecureOne directory.
        response2 = requests.get(f'https://{appliance}:{INI.api_port}/mgmt/filestore/default{INI.secure_path}', auth=INI.authinfo, verify=False)
        file_list = response2.json().get("filestore").get("location").get("file")
        
        # Loop the list to download base64 file and convert into the desired extension
        for item in file_list:
            file_name = item['name']
            #Downloading the file based on list item
            get_file_response = requests.get(f"https://{appliance}:{INI.api_port}{item['href']}", auth=INI.authinfo, verify=False)

            # Create variables for downloaded endode file and where to decode it.
            
            enc_file = f"{secure_enc_dir}/{file_name}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
            dec_file = f"{secure_main_dir}/{file_name}"

            # Open a file with the name of actual file and full path where to write the file
            with open(enc_file, "w") as file_name:
                # identify the "file" key which containes the base64 data of the file and write into the hidden encodedfiles folder
                file_name.write(get_file_response.json().get('file'))

                # Wait for some time till the base64 file gets downloaed and converted.
            
            cmd = (f"base64 -d {enc_file} > {dec_file}")
            os.popen(cmd)
            
            
        print(f"\n{colored('INFO: ', 'green')}Taking SecureBackup is completed on {appliance}")

    else: 
        print(f"\n{colored('ERROR: ', 'red')}Secure backup is failed. {request_status.json().get('error')}")
        

    
   


def main():
    pass
if __name__=="__main__":
    main()
