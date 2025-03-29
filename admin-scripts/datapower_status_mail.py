import pandas as pd
from pretty_html_table import build_table
from dpmodules import ini as INI
from dpmodules import Status as STATS
import requests, smtplib, sys, argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yagmail
parser = argparse.ArgumentParser()


def get_mpgw(appliance, sort_option='ProbStatus'):
    
    html_final = ""
    
    # Check the given host is valid or not
    STATS.ishost_valid(appliance)
    
    domain_list = STATS.get_domain_names(appliance)
    
    # Loop the logic based on domain list collected from above
    for domain_item in domain_list:
        
        # Table related Variables
        table_name = f"MPGW Services on Domain: {domain_item} - Host: {appliance}"
        table_header = ['MPGW_Name', 'FSHDetails', 'BackendURL', 'AdminState', 'OpStatus', 'ErrorCode', 'ProbStatus']
        
        # Empty List of MPGW Objects
        table_data_list = []
        
        # Empty Object status list and call and stores all objects available in appliance
        objstatus_list = []
        objstatus_url = f"https://{appliance}:5554/mgmt/status/{domain_item}/ObjectStatus"
        
        # If user given object name as 'all', we need to call the below url. else call else part
        mpgw_url = f"https://{appliance}:5554/mgmt/config/{domain_item}/MultiProtocolGateway"
        
        # Call and Store the response of all MPGW 
        mpgw_response = requests.get(mpgw_url, auth=(INI.authinfo), verify=False)
        
        # Act based on response code
        
        # if response code is 200, Then only proceed for next actions
        if mpgw_response.status_code == 200:
            
            # Check how many MPGW services occured and store the out put in mpgw_result variable
            mpgw_result = mpgw_response.json().get('MultiProtocolGateway')
            
            # Call the all objects info. We need to exicute this step only at this stage to avoid un nessery call and store big status data
            objstatus_response = requests.get(objstatus_url, auth=(INI.authinfo), verify=False)
            
            # if no mpgw close, call the table with empty data
            if mpgw_result == None:
                table_data_list.append(['No MPGW Service', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'])
                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
            
            # If the return mpgw_list is dict Means only one mpgw service available, call this block.
            elif type(mpgw_result) is dict:
                
                # Find the corrospond Front side handler from above given mpgw_list object
                if 'FrontProtocol' in mpgw_result:
                    mpgw_fsh_list = mpgw_result.get('FrontProtocol')
                    mpgw_fsh_details = []
                    
                    # If only one front side handler occured for given mpgw service, find the url for that fsh and store the response
                    if type(mpgw_fsh_list) is dict:
                        mpgw_fsh_url = f"https://{appliance}:5554{mpgw_fsh_list.get('href')}"
                        mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                        mpgw_fsh_details.append(f"{mpgw_fsh_list.get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                    
                    # If multiple Frontside handler presneted in the given MPGW service.
                    elif type(mpgw_fsh_list) is list:
                        for mpgw_fsh_idx in range(len(mpgw_fsh_list)):
                            mpgw_fsh_url = f"https://{appliance}:5554{mpgw_fsh_list[mpgw_fsh_idx].get('href')}"
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
                table_data_list.append([mpgw_result['name'],
                                        mpgw_fsh_details,
                                        'Dynamic-Backend' if mpgw_result['Type'] == 'dynamic-backend' else mpgw_result['BackendUrl'],
                                        objstatus_list[0]['AdminState'],
                                        objstatus_list[0]['OpState'],
                                        objstatus_list[0]['ErrorCode'],
                                        mpgw_result['DebugMode']])
                    
                # Finally call the helper function to publish the table on console
                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
                
            # If the multiple mpgw services selected, go with below logic
            elif type(mpgw_result) is list:
                
                # Loop each mpgw service and construct each line of table
                for mpgw_idx, mpgw_val in enumerate(mpgw_result):
                    
                    
                    # collect the front side handlers info
                    if 'FrontProtocol' in mpgw_result[mpgw_idx]:
                        mpgw_fsh_list = mpgw_val['FrontProtocol']
                        mpgw_fsh_details = []
                        
                    if type(mpgw_fsh_list) is dict:
                        mpgw_fsh_url = f"https://{appliance}:5554{mpgw_fsh_list.get('href')}"
                        mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                        mpgw_fsh_details.append(f"{mpgw_fsh_list.get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                        
                    elif type(mpgw_fsh_list) is list:
                        for i in range(len(mpgw_fsh_list)):
                            mpgw_fsh_url = f"https://{appliance}:5554{mpgw_fsh_list[i].get('href')}"
                            mpgw_fsh_response = requests.get(mpgw_fsh_url, auth=(INI.authinfo), verify=False)
                            mpgw_fsh_details.append(f"{mpgw_fsh_list[i].get('value')}:{mpgw_fsh_response.json().get(mpgw_fsh_url.split('/')[(-2)]).get('LocalPort')}")

                    else:
                        mpgw_fsh_details.append('No Front Side Handlers')
                        
                    # compare the static properties with running properties like statuses
                    for mpgw_cls in objstatus_response.json().get('ObjectStatus'):
                        if mpgw_cls['Class'] == 'MultiProtocolGateway' and mpgw_cls['Name'] == mpgw_val['name']:
                            objstatus_list.append(mpgw_cls)

                    # Construct the table data
                    table_data_list.append([mpgw_val['name'],
                                           mpgw_fsh_details,
                                           'Dynamic-Backend' if mpgw_val['Type'] == 'dynamic-backend' else mpgw_val['BackendUrl'],
                                           objstatus_list[mpgw_idx]['AdminState'],
                                           objstatus_list[mpgw_idx]['OpState'],
                                           objstatus_list[mpgw_idx]['ErrorCode'],
                                           mpgw_val['DebugMode']])

                # Finally call the helper funcation to publish the table on console
                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
                
    subj = f"MPGW Service Status on {appliance}"
    #send_mail(html_final, subj)
    send_yagmail(html_final, subj)
    
    
# Function to collect the wsp data
def get_wsp(appliance, sort_option='ProbStatus'):
    
    html_final = ""
    
    # Check is host valid or not
    STATS.ishost_valid(appliance)
    
    domain_list = STATS.get_domain_names(appliance)
    
    # Loop the logic against all domains to collect metrics
    for domain_item in domain_list:
        table_name = f"WSP Services on Domain: {domain_item} - Host: {appliance}"
        table_header = ['WSP_Name', 'FSHDetails', 'BackendURL', 'AdminState', 'OpStatus', 'ErrorCode', 'ProbStatus']
        table_data_list = []
        objstatus_list = []
        objstatus_url = f"https://{appliance}:5554/mgmt/status/{domain_item}/ObjectStatus"
        
        # if all domains use below url
        wsp_url = f"https://{appliance}:5554/mgmt/config/{domain_item}/WSGateway"
        
        # Get the wsp data from datapower
        wsp_response = requests.get(wsp_url, auth=(INI.authinfo), verify=False)
        
        # Act based on response code. in this case exit if response code is 404
            
        # if response code is 200, Then only proceed for next actions
        if wsp_response.status_code == 200:
            wsp_result = wsp_response.json().get('WSGateway')
            objstatus_response = requests.get(objstatus_url, auth=(INI.authinfo), verify=False)
            
            # If the nothing is recorded, then call table function with empty
            if wsp_result == None:
                table_data_list.append(['No WSP Service', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'])
                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
            
            elif type(wsp_result) is dict:
                    
                endpoint_url = f"https://{appliance}:5554{wsp_result.get('EndpointRewritePolicy').get('href')}"
                endpoint_result = requests.get(endpoint_url, auth=INI.authinfo, verify=False)
                RewriteRule_list = endpoint_result.json().get('WSEndpointRewritePolicy').get('WSEndpointLocalRewriteRule')
                    
                wsp_fsh_details = []
                    
                if type(RewriteRule_list) is dict:
                    if 'FrontProtocol' in RewriteRule_list:
                        wsp_fsh_list = RewriteRule_list.get('FrontProtocol')
                        wsp_fsh_url = f"https://{appliance}:5554{wsp_fsh_list.get('href')}"
                        wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                        wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                            
                elif type(RewriteRule_list) is list:
                    for rwr_idx, rwr_val in enumerate(RewriteRule_list):
                            
                        if 'FrontProtocol' in RewriteRule_list[rwr_idx]:
                            wsp_fsh_list = rwr_val['FrontProtocol']
                            wsp_fsh_url = f"https://{appliance}:5554{wsp_fsh_list.get('href')}"
                            wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                            wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                else:
                    wsp_fsh_details.append('No Front Side Handlers')
                    
                for wsp_cls in objstatus_response.json().get('ObjectStatus'):
                    if wsp_cls['Class'] == 'WSGateway' and wsp_cls['Name'] == wsp_result['name']:
                        objstatus_list.append(wsp_cls)

                table_data_list.append([wsp_result['name'],
                                    wsp_fsh_details,
                                    wsp_result['Type'],
                                    objstatus_list[0]['AdminState'],
                                    objstatus_list[0]['OpState'],
                                    objstatus_list[0]['ErrorCode'],
                                    wsp_result['DebugMode']])
                
                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
                
            elif type(wsp_result) is list:
                for wsp_idx, wsp_val in enumerate(wsp_result):
                        
                    endpoint_url = f"https://{appliance}:5554{wsp_result[wsp_idx].get('EndpointRewritePolicy').get('href')}"
                    endpoint_result = requests.get(endpoint_url, auth=INI.authinfo, verify=False)
                    RewriteRule_list = endpoint_result.json().get('WSEndpointRewritePolicy').get('WSEndpointLocalRewriteRule')
                                                
                    wsp_fsh_details = []
                    
                    if type(RewriteRule_list) is dict:
                        
                        if 'FrontProtocol' in RewriteRule_list:
                            wsp_fsh_list = RewriteRule_list.get('FrontProtocol')
                            wsp_fsh_url = f"https://{appliance}:5554{wsp_fsh_list.get('href')}"
                            wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                            wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                            
                    elif type(RewriteRule_list) is list:
                        for rwr_idx, rwr_val in enumerate(RewriteRule_list):
                            
                            if 'FrontProtocol' in RewriteRule_list[rwr_idx]:
                                wsp_fsh_list = rwr_val['FrontProtocol']
                                wsp_fsh_url = f"https://{appliance}:5554{wsp_fsh_list.get('href')}"
                                wsp_fsh_response = requests.get(wsp_fsh_url, auth=(INI.authinfo), verify=False)
                                wsp_fsh_details.append(f"{wsp_fsh_list.get('value')}:{wsp_fsh_response.json().get(wsp_fsh_url.split('/')[(-2)]).get('LocalPort')}")
                    else:
                        wsp_fsh_details.append('No Front Side Handlers')
                        
                        
                    for wsp_cls in objstatus_response.json().get('ObjectStatus'):
                        if wsp_cls['Class'] == 'WSGateway' and wsp_cls['Name'] == wsp_val['name']:
                            objstatus_list.append(wsp_cls)


                    table_data_list.append([wsp_result[wsp_idx]['name'],
                                wsp_fsh_details,
                                wsp_result[wsp_idx]['Type'],
                                objstatus_list[wsp_idx]['AdminState'],
                                objstatus_list[wsp_idx]['OpState'],
                                objstatus_list[wsp_idx]['ErrorCode'],
                                wsp_result[wsp_idx]['DebugMode']])

                html_final = html_final + f"<h3>{table_name}</h3>"
                html_final = html_final + generate_html(table_header, table_data_list)
                
    subj = f"WSP Service Status on {appliance}"
    #send_mail(html_final, subj)
    send_yagmail(html_final, subj)
    
def generate_html(table_header, list_obj):
    
    data = pd.DataFrame(list_obj)
    data.columns = table_header
    
    output = build_table(data, 'yellow_dark', even_bg_color='white', even_color='black')
    return output

        
def send_mail(html_content, emailsubject):
    msgPart = MIMEText(html_content, 'html')
    sendFrom = 'Purchase Update <admin@cyberkeeda.com>'
    sendTo = 'customer@cyberkeeda.com'
    # Create the root message and fill in the from, to, and subject headers
    msg = MIMEMultipart('alternative')
    msg['Subject'] = emailsubject
    msg['From'] = sendFrom
    msg['To'] = sendTo
    msg.attach(msgPart)
    
    smtp = smtplib.SMTP('smtp.cyberkeeda.com')
    smtp.sendmail(sendFrom, sendTo, msg.as_string())
    smtp.quit()
    
def send_yagmail(html_content, emailsubject):
    user = 'microaxle.dp01@gmail.com'
    app_password = 'ogosfhlvfjfozsug' # a token for gmail
    to = 'annu.post@outlook.com'

    subject = emailsubject
    content = html_content

    with yagmail.SMTP(user, app_password) as yag:
        yag.send(to, subject, content)
        print('Sent email successfully')

def main():
    # It helps to avoid python warnings which helps us to ignore tls signer authentication

    if not sys.warnoptions:
        import warnings
        warnings.simplefilter("ignore")

    # Default, Mandatary and optional arguments while calling the program
    parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True)
    # parse and store all the user arguments into 'args' variable
    args = parser.parse_args()

    # Once get the domain list based on User choice, loop the list and generate the mpgw status report
    
    get_mpgw(appliance=args.appliance)
    get_wsp(appliance=args.appliance)
    



if __name__ == '__main__':
    main()
