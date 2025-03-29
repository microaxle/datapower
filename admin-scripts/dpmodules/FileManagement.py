from dpmodules import Config as CONFIG
from dpmodules import Helper as HELPER
from dpmodules import Status as STATS
from dpmodules import ini as INI
from termcolor import colored
import os
import sys
from datetime import datetime
import requests
import json

def create_dir(appliance, domain, path):
    
    STATS.ishost_valid(appliance)
    STATS.isdomain_available(appliance, domain)
    
    # we need to devide the base directory of datapower, then only we can make call to create user directories
    # Spliting with / and take first part as base dir and rest the part as user directory path

    #Take user directory path
    tempdict = path.split('/')[1:]
    
    # Join the part with / to make final output of user direcotory path
    userdir = '/'.join(tempdict[0:])

    # if the userdir is empty, alert caller to give correct directory of his/her choice
    if (not userdir):
        print(f"{colored('INFO: ', 'red')}", f"Make sure you given correct path {path}\n")
        sys.exit()
    
    # if the userdir is proper then construct the reuqest payload with user dir
    request_payload = {"directory": 
                            {"name": userdir}
                      }
    
    # As we mentioned above, extracting base path is importent here as we post the request payload to only the base directory of datapower
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/filestore/{domain}/{path.split('/')[0]}"

    # Calling the datapower to create dir
    response = requests.post(operation_url, auth=INI.authinfo, data=json.dumps(request_payload), verify=False)
    
    if response.status_code == 201 and 'result' in response.json():
        print(f"{colored('INFO: ', 'green')}", f"The directory is created in {path}\n")
        
    elif response.status_code == 409 and 'error' in response.json():
        print(f"{colored('ERROR: ', 'red')}", f"The directory  is already exists\n")

def backup_dir(appliance, domain, dirpath):

    STATS.ishost_valid(appliance)
    STATS.isdomain_available(appliance, domain)
    
    operation_url = f'https://{appliance}:{INI.api_port}/mgmt/filestore/{domain}/{dirpath}'

    response = requests.get(operation_url, auth=INI.authinfo, verify=False)
    
    if response.status_code == 404:
        print(f"{colored('ERROR: ', 'red')}", f"No resource found with the name of {dirpath}\n")
        sys.exit()
    
    file_list = response.json().get("filestore").get("location").get("file")
    
    # Loop the list to download base64 file and convert into the desired extension
    if file_list == None:
        print(f"{colored('ERROR: ', 'red')}", f"No files available on {dirpath}\n")

    if not os.path.exists(f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/FileManagement/{dirpath}"):
        os.makedirs(f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/FileManagement/{dirpath}")
    
    if not os.path.exists(f"{INI.code_base}/{appliance}/{domain}/FileManagement/{dirpath}"):
        os.makedirs(f"{INI.code_base}/{appliance}/{domain}/FileManagement/{dirpath}")


    if type(file_list) is dict:
        get_file_response = requests.get(f"https://{appliance}:{INI.api_port}{file_list['href']}", auth=INI.authinfo, verify=False)
        enc_file = f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/FileManagement/{dirpath}/{file_list['name']}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
        dec_file = f"{INI.code_base}/{appliance}/{domain}/FileManagement/{dirpath}/{file_list['name']}"

        # Open a file with the name of actual file and full path where to write the file
        with open(enc_file, "w") as file_list['name']:
            # identify the "file" key which containes the base64 data of the file and write into the hidden encodedfiles folder
            file_list['name'].write(get_file_response.json().get('file'))

            # Wait for some time till the base64 file gets downloaed and converted.
            
        cmd = (f"base64 -d {enc_file} > {dec_file}")
        os.popen(cmd)

        print(f"{colored('INFO: ', 'green')}", f"The directory {dirpath} is downloaded\n")
    elif type(file_list) is list:
        for item in file_list:
            
            file_name = item['name']
            #Downloading the file based on list item
            get_file_response = requests.get(f"https://{appliance}:{INI.api_port}{item['href']}", auth=INI.authinfo, verify=False)

            # Create variables for downloaded endode file and where to decode it.
            
            enc_file = f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/FileManagement/{dirpath}/{file_name}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
            dec_file = f"{INI.code_base}/{appliance}/{domain}/FileManagement/{dirpath}/{file_name}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"


            # Open a file with the name of actual file and full path where to write the file
            with open(enc_file, "w") as file_name:
                # identify the "file" key which containes the base64 data of the file and write into the hidden encodedfiles folder
                file_name.write(get_file_response.json().get('file'))

                # Wait for some time till the base64 file gets downloaed and converted.
            
            cmd = (f"base64 -d {enc_file} > {dec_file}")
            os.popen(cmd)
    
        print(f"{colored('Info: ', 'green')}", f"The directory {dirpath} is downloaded\n")


def backup_file(appliance, domain, filepath):
    STATS.ishost_valid(appliance)
    STATS.isdomain_available(appliance, domain)
        
    operation_url = f'https://{appliance}:{INI.api_port}/mgmt/filestore/{domain}/{filepath}'
    response = requests.get(operation_url, auth=INI.authinfo, verify=False)

    if response.status_code == 403:
        print(f"{colored('ERROR: ', 'red')}", f"Forbidden - You can not download file from cert loation {filepath}\n")
        sys.exit()

    if response.status_code == 404:
        print(f"{colored('ERROR: ', 'red')}", f"No resource found with the name of {filepath}\n")
        sys.exit()

    if response.json().get('file') == None:
        print(f"{colored('ERROR: ', 'red')}", f"file absolute path did not provided {filepath}\n")
        sys.exit()

    file_name = f"{operation_url.split('/')[-1]}"
    
    default_localpath = f"{INI.code_base}/{appliance}/{domain}/FileManagement/{os.path.dirname(filepath)}"
    enc_localpath = f"{INI.code_base}/.encodedfiles/{appliance}/{domain}/FileManagement/{os.path.dirname(filepath)}"
    
    if not os.path.exists(f"{default_localpath}"):
        os.makedirs(f"{default_localpath}")
    
    if not os.path.exists(f"{enc_localpath}"):
        os.makedirs(f"{enc_localpath}")

    
    enc_file = f"{enc_localpath}/{file_name}-{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
    dest_file = f"{default_localpath}/{file_name}_{datetime.now().strftime('%I%M%S%p')}"

    with open(enc_file, "w") as tmp_file:
        # identify the "file" key which containes the base64 data of the file and write into the hidden encodedfiles folder
        tmp_file.write(response.json().get('file'))

    cmd = (f"base64 -d {enc_file} > {dest_file}")
    os.popen(cmd)

    print(f"{colored('Info: ', 'green')}", f"The file {default_localpath}/{file_name} is downloaded\n")
   

def deploy_file(appliance, domain, targetpath, filepath, overwrite):
    HELPER.check_file_exists(filepath)
    STATS.ishost_valid(appliance)
    STATS.isdomain_available(appliance, domain)
        
    file_name = f"{filepath.split('/')[-1]}"

    request_payload = {
                    "file": {
                         "name": file_name,
						 "content":"base64-encoded BLOB"
                        }
                    }
    # save base64 command in a variable.
    cmd = "base64 " + str(filepath)

    # This line converts zip file into base64 by calling os.popen function and inserts the output into the request data dictionory.
    request_payload["file"]["content"] = os.popen(cmd).read()

    if overwrite == 'off':
        operation_url = f"https://{appliance}:{INI.api_port}/mgmt/filestore/{domain}/{targetpath}"
        response = requests.post(operation_url, auth=INI.authinfo, data=json.dumps(request_payload), verify=False)
    else:
        operation_url = f"https://{appliance}:{INI.api_port}/mgmt/filestore/{domain}/{targetpath}/{file_name}" 
        response = requests.put(operation_url, auth=INI.authinfo, data=json.dumps(request_payload), verify=False)
        
    if (response.status_code == 200 or response.status_code == 201) and 'result' in response.json():
        print(f"{colored('INFO: ', 'green')}", f"The file {file_name} is deployed\n")
        CONFIG.save_config(appliance, domain)
    
    if response.status_code == 409 and 'error' in response.json():
        print(f"{colored('ERROR: ', 'red')}", f"{response.json().get('error')}\n")

    if response.status_code == 403:
        print(f"{colored('ERROR: ', 'red')}", f"{targetpath} is not found\n")



def main():
    pass
if __name__=="__main__":
    main()
