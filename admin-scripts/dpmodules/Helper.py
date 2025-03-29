import base64
from dpmodules import ini as INI
import requests
import json
import os
from termcolor import colored
from prettytable import PrettyTable, SINGLE_BORDER, ALL

def check_file_exists(file):
    if os.path.exists(file):
        pass
    else: quit(f"\n{colored('ERROR: ', 'red')} The given file {file} is not found\n")
    

def generate_table(table_name, table_header, list_obj, sort_option):
    tb = PrettyTable()
    tb.header = True
    tb.field_names = table_header
    tb.add_rows(list_obj)
    tb.hrules = ALL
    tb.set_style(SINGLE_BORDER)
    #tb.set_style(DOUBLE_BORDER)
    #tb.set_style(ORGMODE)
    #tb.set_style(MARKDOWN)
    #tb.set_style(PLAIN_COLUMNS)
    print("")
    print(tb.get_string(title=table_name, sortby=sort_option))
        
def get_base_resources(hostname):
    response = requests.get(f"{hostname}:5554/mgmt/", verify=False)
    response_object = response.json()
    
    print("Printing response_object....................")
    print(response_object)

    formatted_response = json.dumps(response_object, indent=4, sort_keys=True)
    print("Printing formatted_response..................")
    print(formatted_response)

def encode_to_base64(data):
    encoded_string = base64.b64encode(data.encode("utf-8"))
    return encoded_string
    #print(base64.b64decode(b'SmFpMTBAcHJk').decode('utf-8'))

def decode_from_base64(data):
    decoded_string = base64.b64decode(data).decode('utf-8')
    return decoded_string

def get_object_class(appliance, domain, object_name):
    response = requests.get(f"https://{appliance}:{INI.api_port}/mgmt/status/{domain}/ObjectStatus", auth=INI.authinfo, verify=False)
    
    for item in response.json().get('ObjectStatus'):
        if item['Name'] == object_name:
            return item['Class']

        
    


def main():
   pass
if __name__=="__main__":
    main()
