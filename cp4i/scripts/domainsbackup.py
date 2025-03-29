"""
Author: annu.singh@ralphlauren.com
Date: 2024-Aug-23
Description: The script is for taking all domains backup from CP4I datapower.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64, os, time, json, requests, argparse, smtplib, sys
from datetime import datetime
from time import sleep
from termcolor import colored

# This package helps us to load the properties file and parse the values.
from jproperties import Properties
configs = Properties()

# This package helps us to accept and validate input flag values
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Get the directory containing the current script.
script_location = os.path.dirname(os.path.realpath(__file__))

# Move one step back from the current directory.
dp_homepath = os.path.abspath(os.path.join(script_location, os.pardir))

if not os.path.exists(f"{script_location}/logs"):
    os.makedirs(f"{script_location}/logs")

if not os.path.exists(f"{dp_homepath}/backups"):
    os.makedirs(f"{dp_homepath}/backups")

# Once fine the script location, load properties file from the config location. this helps user to keep these scripts home folder any where in the system.
with open(f"{script_location}/dp-config.properties", 'rb') as config_file:
    configs.load(config_file)

# Load all the required custom values from the properties file.
code_base = f"{dp_homepath}/backups"
authinfo = (configs.get("user").data, base64.b64decode(configs.get("cred").data).decode("utf-8"))
tmp_dir = f"{code_base}/.tmp"
#api_port = int(configs.get("api_port").data)
#api_port is not required for CP4I

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



# In order to work with dp and to provide more customization, first we need to identify the available domains.
def get_domain_names(appliance):

    # Once the appliance is valid and pingable, call the dp REST SERVICE with below resource and parse to find all available domains
    response = requests.get(f"https://{appliance}/mgmt/domains/config/", auth=(authinfo), verify=False)
    domains_object = response.json().get('domain')

    # Initialize the empty list to store all availabel domains
    domain_names = []

    # If we have only one domain, the response contains dic object, so we need to take the name of single domain and append to the empty list.
    # We are also creating folder based on domain to store all domain related data into the appropriate domain folder.
    if type(domains_object) is dict:
        domain_names.append(domains_object['name'])
        if not os.path.exists(f"{code_base}/{appliance}/DomainBackups/{domains_object['name']}"):
            os.makedirs(f"{code_base}/{appliance}/DomainBackups/{domains_object['name']}")
        if not os.path.exists(f"{code_base}/.encodedfiles/{appliance}/DomainBackups/{domains_object['name']}"):
            os.makedirs(f"{code_base}/.encodedfiles/{appliance}/DomainBackups/{domains_object['name']}")

    # If the appliance has multiple domains, we get response as List objects. hence we need iterate and append all the available domains into the domain_names list variable.
    elif type(domains_object) is list:
        for item in response.json().get('domain'):
            domain_names.append(item['name'])
            if not os.path.exists(f"{code_base}/{appliance}/DomainBackups/{item['name']}"):
                os.makedirs(f"{code_base}/{appliance}/DomainBackups/{item['name']}")
            if not os.path.exists(f"{code_base}/.encodedfiles/{appliance}/DomainBackups/{item['name']}"):
                os.makedirs(f"{code_base}/.encodedfiles/{appliance}/DomainBackups/{item['name']}")

    #Finally return the domain_names variable which contains the domain names of the datapower.
    return domain_names

# This function helps to verify availability of domain what user provided.
def isdomain_available(appliance, domain):
    # Already logic implemented to get all the domain names from the appliance in get_domain_names() function
    # Hence all get_domain_names() and store the return list of domain
    domain_list = get_domain_names(appliance)

    # Check weather the given domain name is available in the list or not.
    # If Yes, control will go back to caller function, else it will print error and exit the program.
    if domain in domain_list:
        pass
    else:
        print(f"{colored('ERROR: ', 'red')}{domain} domain is not available/accesible\n")
        sys.exit()

# Once all above validations completed, this function works to take backup of domains.
def backup_domains(appliance, domain):

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

    html_content += f"<h2>CP4I Datapower Backup Report - PROD</h2>"
    html_content += """
        <table>
            <tr>
                <th>Appliance</th>
                <th>Domain</th>
                <th>Status</th>
                <th>File</th>
            </tr>
        """

    # Creating empty list variable to loop the domain wise action
    domain_list = []

    # If user provides a domain name, then it will call isdomain_available() function to check the given domain name correct or not.
    # Program will exit in isdomain_available() function itself, if the given domain name not available in the appliance
    if domain != "all":
        isdomain_available(appliance, domain)
        domain_list.append(domain)

    # if user chooses all domains, then no need to validate the domain names, instead connect appliance and get all the available domain names.
    if domain == "all":
        domain_list = get_domain_names(appliance)

    # Once we ready with domain_list variable, will loop to perform action on each domain.
    for item in domain_list:
        # Just calling item as domain for better understand.
        domain = item
        # This is the request msg which will be sent to the appliance.
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
        # This is the URL of DataPower for backup action
        operation_url = f"https://{appliance}/mgmt/actionqueue/default"

        # We get/download only encoded files from datapower. Hence store it on linux box first, then decode the file for human readable
        # Hence creating both locations for encode and decode files
        encode_file = f"{code_base}/.encodedfiles/{appliance}/DomainBackups/{domain}/{domain}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}"
        decode_file = f"{code_base}/{appliance}/DomainBackups/{domain}/{domain}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.zip"

        # Finally calling datapower to get the domain backup
        response = requests.post(operation_url, data=json.dumps(request_payload, indent = 4), auth=authinfo, verify=False)

        # If the above request accepts, then will proceed for next action to calculate time to complete the request.
        if response.status_code == 202:

            # Important : When we send domain backup request using REST service, Datapower will accept the request and send back the Action status API.
            # We need to use the given Action Status API and wait for completed status
            f_location = response.json().get('_links').get('location').get('href')

            #get_file = requests.get(f"https://{appliance}{f_location}", auth=authinfo, verify=False)

            # Initialize the start time
            start_time = time.time()

            # Set the update frequency (e.g., every 1 second)
            update_interval = 1

            while True:
                get_file = requests.get(f"https://{appliance}{f_location}", auth=authinfo, verify=False)
                # Calculate the elapsed time
                elapsed_time = time.time() - start_time

                progress_bar = f"Back up {domain} domain is in Progress : "

                # Print the progress bar and elapsed time on the same line using carriage return
                print(f"\r{progress_bar} Time Taken: {elapsed_time:.2f} seconds", end="")

                # Sleep for the specified update interval
                time.sleep(update_interval)

                if get_file.json().get('status') == 'completed':
                    with open(f"{encode_file}", "w") as file1:
                        file1.write(get_file.json().get('result').get('file'))
                    sleep(2)
                    cmd = (f"base64 -d {encode_file} > {decode_file}")
                    os.popen(cmd)
                    print(f"\n{colored('INFO: ', 'green')}file \'{decode_file}\' is downloaded successfully.\n")
                    html_content += f"""
                            <tr>
                                <td>{appliance}</td>
                                <td>{domain}</td>
                                <td>Completed</td>
                                <td>{domain}_{datetime.now().strftime('%Y_%m_%d-%I_%M_%S_%p')}.zip</td>
                            """
                    break
        else:
            print('Request not accepted..')
            html_content += f"""
                            <tr>
                                <td>{appliance}</td>
                                <td style="background-color: #f44336; color: white;">Failed</td>
                                <td>Failed</td>
                                """

    html_content += """
        </table>
        </body>
        </html>
        """
    #print(html_content)

    email_subject = f"CP4I Datapower Backup Report - PROD"
    send_mail(html_content, email_subject)

def send_mail(html_content, emailsubject):
    msgPart = MIMEText(html_content, 'html')
    sendFrom = 'Datapower-Backup-Report@poloralphlauren.com'
    sendTo = ['RL-OMS-Regionalization-Team@prolifics.com', 'DL-Group-IT-ESB-Middleware-Support@RalphLauren.com', 'annu.singh@ralphlauren.com', 'annu.singh@prolifics.com']
    #sendTo = ['annu.singh@ralphlauren.com']
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
    backup_domains(args.appliance, args.domain)

if __name__ == "__main__":
    main()


