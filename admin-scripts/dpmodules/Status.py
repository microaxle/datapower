from dpmodules import Helper as HELPER
from dpmodules import ini as INI
import requests, os, sys
from colorama import Back, Fore, Style
from termcolor import colored

def check_user(appliance):
    
    # Simply call a active users api where authentication is required and validate the response
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/status/default/ActiveUsers"
    response = requests.get(operation_url, auth=INI.authinfo, verify=False)
    result = response.json()

    if 'error' in result:
        print(f"{colored('ERROR: ', 'red')} Provided Credentials are not valid\n")
        sys.exit()
    else:
        pass
    
# Get the check point list from given appliance
def get_checkpoint_list(appliance, domain):
    
    # Check the given appliance is available or not by calling another function
    ishost_valid(appliance)
    
    # Check the given domain is valid or not by calling another function.
    isdomain_available(appliance, domain)
    
    # Create Empty table list to store the checkpoint data.
    table_data = []
    
    # Design the table
    table_name = Fore.YELLOW + f"Checkpoint Status on {Fore.MAGENTA}{domain}" + Style.RESET_ALL
    table_header = ['CreateDate', 'CreateTime', 'CheckPointName']
    sort_option = 'CreateTime'
    
    # Below is the operational url of datapower to get check point information
    operation_url = f"https://{appliance}:{INI.api_port}/mgmt/status/{domain}/DomainCheckpointStatus"
    response = requests.get(operation_url, auth=(INI.authinfo), verify=False)
    
    # Parse and store the json response in python object.
    response_obj = response.json().get('DomainCheckpointStatus')
    
    # Act based on return code
    # Check the object type to identity if any data returned or not
    if response.status_code == 200 and  isinstance(response_obj, type(None)):
        print(f"\n{colored('INFO: ', 'green')} No CheckPoints available on {domain} domain")
        table_data.append(['n/a', 'n/a', 'n/a'])
        HELPER.generate_table(table_name, table_header, table_data, sort_option)
        return True
    
    elif response.status_code == 200 and isinstance(response_obj, dict):
        table_data.append([response_obj['Date'], response_obj['Time'], response_obj['ChkName']])
        HELPER.generate_table(table_name, table_header, table_data, sort_option)
        return False
    
    elif response.status_code == 200 and isinstance(response_obj, list):
        for item in response_obj:
            table_data.append([item['Date'], item['Time'], item['ChkName']])
        HELPER.generate_table(table_name, table_header, table_data, sort_option)
        return False


def get_object_info(appliance, domain, obj_name):
    ishost_valid(appliance)
    isdomain_available(appliance, domain)
    obj_info = []
    response = requests.get(f"https://{appliance}:{INI.api_port}/mgmt/status/{domain}/ObjectStatus", auth=(INI.authinfo), verify=False)
    if response.status_code == 401:
        exit('Error: Authentication Failure')
    if response.status_code == 200:
        
        if obj_name == 'all':
            return response.json().get('ObjectStatus')
            
        else:
            for item in response.json().get('ObjectStatus'):
                if item['Name'] == obj_name:
                    obj_info.append(item)
        
        # Check the variable is empty or having data. if it is empty throw custom message else return the value.
        if obj_info:
            return obj_info
        print(f"{colored('ERROR: ', 'red')}No Object available with given name {obj_name}\n")
        sys.exit()


def ishost_valid(appliance):
    try:
        requests.get(f"https://{appliance}:{INI.api_port}/mgmt/", verify=False)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def isdomain_available(appliance, domain):
    domain_list = get_domain_names(appliance)
    if domain in domain_list:
        pass
    else:
        print(f"{colored('ERROR: ', 'red')}{domain} domain is not available/accesible\n")
        sys.exit()


def get_domain_names(appliance):
    
    # Verify the given appliance is valid or not
    ishost_valid(appliance)
    
    # Once the appliance is valid and pingable, call the dp REST SERVICE with below resource
    response = requests.get(f"https://{appliance}:{INI.api_port}/mgmt/domains/config/", auth=(INI.authinfo), verify=False)
    domains_object = response.json().get('domain')
    
    domain_names = []
    if type(domains_object) is dict:
        domain_names.append(domains_object['name'])
        if not os.path.exists(f"{INI.code_base}/{appliance}/{domains_object['name']}"):
            os.makedirs(f"{INI.code_base}/{appliance}/{domains_object['name']}")
        if not os.path.exists(f"{INI.code_base}/.encodedfiles/{appliance}/{domains_object['name']}"):
            os.makedirs(f"{INI.code_base}/.encodedfiles/{appliance}/{domains_object['name']}")
    elif type(domains_object) is list:
        for item in response.json().get('domain'):
            domain_names.append(item['name'])
            if not os.path.exists(f"{INI.code_base}/{appliance}/{item['name']}"):
                os.makedirs(f"{INI.code_base}/{appliance}/{item['name']}")
            if not os.path.exists(f"{INI.code_base}/.encodedfiles/{appliance}/{item['name']}"):
                os.makedirs(f"{INI.code_base}/.encodedfiles/{appliance}/{item['name']}")

    return domain_names


def get_mpgw(appliance, domain, object_name, sort_option='ProbStatus'):
    
    # Check the given host is valid or not
    ishost_valid(appliance)
    
    # Make the python list of domains
    if domain == 'all':
        domain_list = get_domain_names(appliance)
    else:
        domain_list = [domain]
        
        #if user gave one domain, make sure the domain is valid or not
        isdomain_available(appliance, domain)
    
    # Loop the logic based on domain list collected from above
    for domain_item in domain_list:
        
        # Table related Variables
        table_name = Fore.YELLOW + f"MPGW Services on Domain: {Fore.MAGENTA}{domain_item} - Host: {appliance}" + Style.RESET_ALL
        table_header = ['MPGW_Name', 'FSHDetails', 'BackendURL', 'AdminState', 'OpStatus', 'ErrorCode', 'ProbStatus']
        
        # Empty List of MPGW Objects
        table_data_list = []
        
        # Empty Object status list and call and stores all objects available in appliance
        objstatus_list = []
        objstatus_url = f"https://{appliance}:{INI.api_port}/mgmt/status/{domain_item}/ObjectStatus"
        
        # If user given object name as 'all', we need to call the below url. else call else part
        if object_name == 'all':
            mpgw_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain_item}/MultiProtocolGateway"
        else:
            mpgw_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain_item}/MultiProtocolGateway/{object_name}"
        
        # Call and Store the response of all MPGW 
        mpgw_response = requests.get(mpgw_url, auth=(INI.authinfo), verify=False)
        
        # Act based on response code
        # Exit with custom msg if 404 returns
        if mpgw_response.status_code == 404:
            print(f"{colored('ERROR: ', 'red')}{object_name} is not found on {domain_item} domain\n")
            sys.exit()
        
        # if response code is 200, Then only proceed for next actions
        if mpgw_response.status_code == 200:
            
            # Check how many MPGW services occured and store the out put in mpgw_result variable
            mpgw_result = mpgw_response.json().get('MultiProtocolGateway')
            
            # Call the all objects info. We need to exicute this step only at this stage to avoid un nessery call and store big status data
            objstatus_response = requests.get(objstatus_url, auth=(INI.authinfo), verify=False)
            
            # if no mpgw close, call the table with empty data
            if mpgw_result == None:
                table_data_list.append(['No MPGW Service', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'])
                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)
            
            # If the return mpgw_list is dict Means only one mpgw service available, call this block.
            elif type(mpgw_result) is dict:
                
                # Find the corrospond Front side handler from above given mpgw_list object
                if 'FrontProtocol' in mpgw_result:
                    mpgw_fsh_list = mpgw_result.get('FrontProtocol')
                    mpgw_fsh_details = []
                    
                    # If only one front side handler occured for given mpgw service, find the url for that fsh and store the response
                    if type(mpgw_fsh_list) is dict:
                        mpgw_fsh_url = f"https://{appliance}:{INI.api_port}{mpgw_fsh_list.get('href')}"
                        mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                        mpgw_fsh_details.append(f"{mpgw_fsh_list.get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                    
                    # If multiple Frontside handler presneted in the given MPGW service.
                    elif type(mpgw_fsh_list) is list:
                        for mpgw_fsh_idx in range(len(mpgw_fsh_list)):
                            mpgw_fsh_url = f"https://{appliance}:{INI.api_port}{mpgw_fsh_list[mpgw_fsh_idx].get('href')}"
                            mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                            mpgw_fsh_details.append(f"{mpgw_fsh_list[mpgw_fsh_idx].get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")

                    # Finally if no front side handler configured for given mpgw service
                    else:
                        mpgw_fsh_details.append('No Front Side Handlers')
                    
                # compare the static properties with running properites like statuses
                for mpgw_cls in objstatus_response.json().get('ObjectStatus'):
                    if mpgw_cls['Class'] == 'MultiProtocolGateway' and mpgw_cls['Name'] == mpgw_result['name']:
                        objstatus_list.append(mpgw_cls)

                # Once we collected all required information, start constructing table list for display
                prob_color = Back.GREEN if mpgw_result['DebugMode'] == 'off' else Back.RED
                OpState_color = Back.GREEN if objstatus_list[0]['OpState'] == 'up' else Back.RED
                table_data_list.append([mpgw_result['name'],
                                        mpgw_fsh_details,
                                        'Dynamic-Backend' if mpgw_result['Type'] == 'dynamic-backend' else mpgw_result['BackendUrl'],
                                        objstatus_list[0]['AdminState'],
                                        OpState_color + objstatus_list[0]['OpState'] + Style.RESET_ALL,
                                        objstatus_list[0]['ErrorCode'],
                                        prob_color + mpgw_result['DebugMode'] + Style.RESET_ALL])
                    
                # Finally call the helper function to publish the table on console
                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)
                
            # If the multiple mpgw services selected, go with below logic
            elif type(mpgw_result) is list:
                
                # Loop each mpgw service and construct each line of table
                for mpgw_idx, mpgw_val in enumerate(mpgw_result):
                    
                    
                    # collect the front side handlers info
                    if 'FrontProtocol' in mpgw_result[mpgw_idx]:
                        mpgw_fsh_list = mpgw_val['FrontProtocol']
                        mpgw_fsh_details = []
                    
                    # if the only one handler available then it will be as dict
                    # call the http handler api and get the details of the fsh   
                    if type(mpgw_fsh_list) is dict:
                        mpgw_fsh_url = f"https://{appliance}:{INI.api_port}{mpgw_fsh_list.get('href')}"
                        mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                        mpgw_fsh_details.append(f"{mpgw_fsh_list.get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                    
                    # if multiple handlers available to the service, then the result will be as list
                    # call the http handler api and get the details of the fsh
                    elif type(mpgw_fsh_list) is list:
                        for i in range(len(mpgw_fsh_list)):
                            mpgw_fsh_url = f"https://{appliance}:{INI.api_port}{mpgw_fsh_list[i].get('href')}"
                            mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                            mpgw_fsh_details.append(f"{mpgw_fsh_list[i].get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")

                    else:
                        mpgw_fsh_details.append('No Front Side Handlers')
                        
                    # compare the static properties with running properties like statuses
                    for mpgw_cls in objstatus_response.json().get('ObjectStatus'):
                        if mpgw_cls['Class'] == 'MultiProtocolGateway' and mpgw_cls['Name'] == mpgw_val['name']:
                            objstatus_list.append(mpgw_cls)

                    # Construct the table data
                    prob_color = Back.GREEN if mpgw_val['DebugMode'] == 'off' else Back.RED
                    OpState_color = Back.GREEN if objstatus_list[mpgw_idx]['OpState'] == 'up' else Back.RED
                    table_data_list.append([mpgw_val['name'],
                                           mpgw_fsh_details,
                                           'Dynamic-Backend' if mpgw_val['Type'] == 'dynamic-backend' else mpgw_val['BackendUrl'],
                                           objstatus_list[mpgw_idx]['AdminState'],
                                           OpState_color + objstatus_list[mpgw_idx]['OpState'] + Style.RESET_ALL,
                                           objstatus_list[mpgw_idx]['ErrorCode'],
                                           prob_color + mpgw_val['DebugMode'] + Style.RESET_ALL])

                # Finally call the helper funcation to publish the table on console
                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)
                

# Function to collect the wsp data
def get_wsp(appliance, domain, object_name, sort_option='ProbStatus'):
    
    # Check if the host valid or not
    ishost_valid(appliance)
    
    # Get domain names
    if domain == 'all':
        domain_list = get_domain_names(appliance)
    else:
        domain_list = [domain]
        isdomain_available(appliance, domain)
    
    # Loop the logic against all domains to collect metrics
    for domain_item in domain_list:
        table_name = Fore.YELLOW + f"WSP Services on Domain: {Fore.MAGENTA}{domain_item} - Host: {appliance}" + Style.RESET_ALL
        table_header = ['WSP_Name', 'FSHDetails', 'BackendURL', 'AdminState', 'OpStatus', 'ErrorCode', 'ProbStatus']
        table_data_list = []
        objstatus_list = []
        objstatus_url = f"https://{appliance}:{INI.api_port}/mgmt/status/{domain_item}/ObjectStatus"
        
        # based on the object selection, get the appropriate url from below block.
        if object_name == 'all':
            wsp_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain_item}/WSGateway"
        else:
            wsp_url = f"https://{appliance}:{INI.api_port}/mgmt/config/{domain_item}/WSGateway/{object_name}"
        
        # Get the wsp data from datapower
        wsp_response = requests.get(wsp_url, auth=(INI.authinfo), verify=False)
        
        # Act based on response code. in this case exit if response code is 404
        if wsp_response.status_code == 404:
            print(f"{colored('ERROR: ', 'red')}{object_name} is not found on {domain_item} domain\n")
            sys.exit()
            
        # if response code is 200, Then only proceed for next actions
        if wsp_response.status_code == 200:
            wsp_result = wsp_response.json().get('WSGateway')
            objstatus_response = requests.get(objstatus_url, auth=(INI.authinfo), verify=False)
            
            # If the nothing is recorded, then call table function with empty
            if wsp_result == None:
                table_data_list.append(['No WSP Service', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'])
                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)
            
            elif type(wsp_result) is dict:
                    
                endpoint_url = f"https://{appliance}:{INI.api_port}{wsp_result.get('EndpointRewritePolicy').get('href')}"
                endpoint_result = requests.get(endpoint_url, auth=INI.authinfo, verify=False)
                RewriteRule_list = endpoint_result.json().get('WSEndpointRewritePolicy').get('WSEndpointLocalRewriteRule')
                    
                wsp_fsh_details = []
                    
                if type(RewriteRule_list) is dict:
                    if 'FrontProtocol' in RewriteRule_list:
                        wsp_fsh_list = RewriteRule_list.get('FrontProtocol')
                        wsp_fsh_url = f"https://{appliance}:{INI.api_port}{wsp_fsh_list.get('href')}"
                        wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                        wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                            
                elif type(RewriteRule_list) is list:
                    for rwr_idx, rwr_val in enumerate(RewriteRule_list):
                            
                        if 'FrontProtocol' in RewriteRule_list[rwr_idx]:
                            wsp_fsh_list = rwr_val['FrontProtocol']
                            wsp_fsh_url = f"https://{appliance}:{INI.api_port}{wsp_fsh_list.get('href')}"
                            wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                            wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                else:
                    wsp_fsh_details.append('No Front Side Handlers')
                    
                for wsp_cls in objstatus_response.json().get('ObjectStatus'):
                    if wsp_cls['Class'] == 'WSGateway' and wsp_cls['Name'] == wsp_result['name']:
                        objstatus_list.append(wsp_cls)

                prob_color = Back.GREEN if wsp_result['DebugMode'] == 'off' else Back.RED
                OpState_color = Back.GREEN if objstatus_list[0]['OpState'] == 'up' else Back.RED
                table_data_list.append([wsp_result['name'],
                                    wsp_fsh_details,
                                    wsp_result['Type'],
                                    objstatus_list[0]['AdminState'],
                                    OpState_color + objstatus_list[0]['OpState'] + Style.RESET_ALL,
                                    objstatus_list[0]['ErrorCode'],
                                    prob_color + wsp_result['DebugMode'] + Style.RESET_ALL])
                
                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)
                
            elif type(wsp_result) is list:
                for wsp_idx, wsp_val in enumerate(wsp_result):
                        
                    endpoint_url = f"https://{appliance}:{INI.api_port}{wsp_result[wsp_idx].get('EndpointRewritePolicy').get('href')}"
                    endpoint_result = requests.get(endpoint_url, auth=INI.authinfo, verify=False)
                    RewriteRule_list = endpoint_result.json().get('WSEndpointRewritePolicy').get('WSEndpointLocalRewriteRule')
                                                
                    wsp_fsh_details = []
                    
                    if type(RewriteRule_list) is dict:
                        
                        if 'FrontProtocol' in RewriteRule_list:
                            wsp_fsh_list = RewriteRule_list.get('FrontProtocol')
                            wsp_fsh_url = f"https://{appliance}:{INI.api_port}{wsp_fsh_list.get('href')}"
                            wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                            wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                            
                    elif type(RewriteRule_list) is list:
                        for rwr_idx, rwr_val in enumerate(RewriteRule_list):
                            
                            if 'FrontProtocol' in RewriteRule_list[rwr_idx]:
                                wsp_fsh_list = rwr_val['FrontProtocol']
                                wsp_fsh_url = f"https://{appliance}:{INI.api_port}{wsp_fsh_list.get('href')}"
                                wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                                wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                    else:
                        wsp_fsh_details.append('No Front Side Handlers')
                        
                        
                    for wsp_cls in objstatus_response.json().get('ObjectStatus'):
                        if wsp_cls['Class'] == 'WSGateway' and wsp_cls['Name'] == wsp_val['name']:
                            objstatus_list.append(wsp_cls)


                    prob_color = Back.GREEN if wsp_result[wsp_idx]['DebugMode'] == 'off' else Back.RED
                    OpState_color = Back.GREEN if objstatus_list[wsp_idx]['OpState'] == 'up' else Back.RED
                    table_data_list.append([wsp_result[wsp_idx]['name'],
                                wsp_fsh_details,
                                wsp_result[wsp_idx]['Type'],
                                objstatus_list[wsp_idx]['AdminState'],
                                OpState_color + objstatus_list[wsp_idx]['OpState'] + Style.RESET_ALL,
                                objstatus_list[wsp_idx]['ErrorCode'],
                                prob_color + wsp_result[wsp_idx]['DebugMode'] + Style.RESET_ALL])

                HELPER.generate_table(table_name, table_header, table_data_list, sort_option)

def main():
    pass


if __name__ == '__main__':
    main()
