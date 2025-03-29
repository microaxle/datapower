"""
Author: annu.singh@ralphlauren.com
Date: 2024-Aug-23
Description: The script helps to dentify downed MQFSH handlers on only from Active Appliance and sends email
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, base64, os, requests, argparse, sys
from datetime import datetime
from time import sleep
from jproperties import Properties
from termcolor import colored

configs = Properties()
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication.
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")


# Get the directory containing the current script.
script_location = os.path.dirname(os.path.realpath(__file__))

# Move one step back from the current directory.
if not os.path.exists(f"{script_location}/logs"):
    os.makedirs(f"{script_location}/logs")

# Once fine the script location, load properties file from the config location. this helps user to keep these scripts home folder any where in the system.
with open(f"{script_location}/dp-config.properties", 'rb') as config_file:
    configs.load(config_file)

# Load all the required custom values from the properties file.
authinfo = (configs.get("user").data, base64.b64decode(configs.get("cred").data).decode("utf-8"))
#api_port = int(configs.get("api_port").data)
# api port is not required for cp4i datapower as it depends on openshift rest route


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

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_mq_handlers_status(appliance, domain):
    domain_list = []
    is_handlers_list_empty = "Need_to_Check"
    qa_appliances = ["dp-rmi-dp-apac.apps.qap.europe.poloralphlauren.com"]
    if appliance in qa_appliances:
        email_subject = f"CP4I-QA - MQ Handlers Report on Openshift QA Pod dp-apac-0 - domain is {domain}"
    else:
        email_subject = f"CP4I-PROD - MQ Handlers Report on openshift PROD Pod dp-apac-0  - domain is {domain}"

    # Create the HTML content dynamically based on the data
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
            }

            h2 {
                text-align: center;
                margin-top: 20px;
                color: #333;
            }

            table {
                border-collapse: collapse;
                width: 80%;
                margin: 0 auto;
                background-color: GhostWhite;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            th, td {
                border: 3px solid #ddd;
                padding: 12px;
                text-align: center;
            }

            th {
                background-color: #2196F3; /* Blue header background color */
                color: white; /* Header text color */
                font-weight: bold; /* Bold header text */
                text-transform: uppercase; /* Uppercase header text */
            }
        </style>
    </head>
    <body>
    """
    html_content += f"<h2>MQ Handlers Report on {appliance} </h2>"
    html_content += """
        <table>
            <tr>
                <th>Appliance</th>
                <th>Domain</th>
                <th>Service</th>
                <th>Admin State</th>
                <th>Operational State</th>
                <th>ErrorCode</th>
            </tr>
        """

    if domain != "all":
        isdomain_available(appliance, domain)
        domain_list.append(domain)

    if domain == "all":
        domain_list = get_domain_names(appliance)

    for domain in domain_list:
        response = requests.get(f"https://{appliance}/mgmt/status/{domain}/ObjectStatus", auth=(authinfo), verify=False)
        list_objects = response.json().get("ObjectStatus")

        mqfsh_list = []
        for item in list_objects:
           if (item['Class'] == 'MQSourceProtocolHandler' or item['Class'] == 'MQv9PlusSourceProtocolHandler') and item['ErrorCode'] != 'in quiescence' and ( item['AdminState'] != 'enabled' or item['OpState'] != 'up'):
              mqfsh_list.append(item)

        if not mqfsh_list:
            continue
        else:
            is_handlers_list_empty = "False"
            table_initiator = 1
            for handler in mqfsh_list:
                if table_initiator == 1:
                    html_content += f"""
                            <tr>
                                <td>{appliance}</td>
                                <td>{domain}</td>
                                <td>{handler['Name']}</td>
                                <td>{handler['AdminState']}</td>
                            """
                    if handler['OpState'] == 'down':
                        html_content += f"""
                            <td style="background-color: #f44336; color: white;">{handler['OpState']}</td>
                            <td>{handler['ErrorCode']}</td>
                            </tr>
                            """
                    elif handler['OpState'] == 'up':
                        html_content += f"""
                            <td style="background-color: #4CAF50; color: white;">{handler['OpState']}</td>
                            <td>{handler['ErrorCode']}</td>
                            </tr>
                            """
                    timestamp = get_timestamp()
                    print(f"{timestamp} Handlers Down Status - Appliance is: {appliance}, Domain is: {domain} ")
                    print(f"{timestamp} Handler: {handler['Name']} - AdminState: {handler['AdminState']} - OpState: {handler['OpState']} - Info: {handler['ErrorCode']}")
                    table_initiator = 0
                else:
                    html_content += f"""
                            <tr>
                                <td></td>
                                <td></td>
                                <td>{handler['Name']}</td>
                                <td>{handler['AdminState']}</td>
                            """
                    if handler['OpState'] == 'down':
                        html_content += f"""
                            <td style="background-color: #f44336; color: white;">{handler['OpState']}</td>
                            <td>{handler['ErrorCode']}</td>
                            </tr>
                            """
                    elif handler['OpState'] == 'up':
                        html_content += f"""
                            <td style="background-color: #4CAF50; color: white;">{handler['OpState']}</td>
                            <td>{handler['ErrorCode']}</td>
                            </tr>
                            """
                    timestamp = get_timestamp()
                    print(f"{timestamp} Handler: {handler['Name']} - AdminState: {handler['AdminState']} - OpState: {handler['OpState']} - Info: {handler['ErrorCode']}")

    html_content += """
        </table>
        </body>
        </html>
    """
    if is_handlers_list_empty == "False":
        send_mail(html_content, email_subject)

def send_mail(html_content, emailsubject):
    msgPart = MIMEText(html_content, 'html')
    sendFrom = 'DP-MQ-FSH-Report@poloralphlauren.com'
    #sendTo = 'annu.singh@prolifics.com'
    sendTo = ['DL-Group-IT-ESB-Middleware-Support@RalphLauren.com', 'annu.singh@ralphlauren.com', 'annu.singh@prolifics.com']
    # Create the root message and fill in the from, to, and subject headers
    msg = MIMEMultipart('alternative')
    msg['Subject'] = emailsubject
    msg['From'] = sendFrom
    msg['To'] = ', '.join(sendTo)
    msg.attach(msgPart)

    smtp = smtplib.SMTP('smtp1.poloralphlauren.com:25')
    smtp.sendmail(sendFrom, sendTo, msg.as_string())
    smtp.quit()


def main():
    parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True)
    parser.add_argument("-d", "--domain", help="Datapower Application Domain or 'all' - It is Required Argument", required=True)

    # parse and store all the user arguments into 'args' variable
    args = parser.parse_args()

    check_user(args.appliance)
    ishost_valid(args.appliance)
    #check_standby_status(args.appliance)
    get_mq_handlers_status(args.appliance, args.domain)

if __name__ == "__main__":
    main()

