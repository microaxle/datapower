from dpmodules import Config as CONFIG
from dpmodules import Status as STATS
import argparse
from termcolor import colored

# Instatiate argparse class. It helps to deal arguments
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Get the inputs from user and parse them 
parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True) 
parser.add_argument("-d", "--domain", help="Datapower Application Domain or 'all' - It is Required Argument", required=True)
parser.add_argument("-o", "--object", help="Service Name or 'all' - It is Required Argument", required=True)
parser.add_argument("-p", "--probe", help="Probe off or on - default value is off", default="off")

# Parse the argument what user provided and store them in args tuple
args = parser.parse_args()

# Initiate Empty List variable to store the available domain names on the appliance.
domain_list = []

# Do not proceed and exit from the program if object is all and enabling prob is not off. 
if args.object == 'all' and args.probe != 'off':
    print(f"{colored('ERROR: ', 'red')} Prob Enabling on all Objects at a time not Allowed.\n")
    sys.exit()

# Do not proceed and exit from the program if domain is all and prob is not set off.
elif args.domain == 'all' and args.probe != 'off':
    print(f"{colored('ERROR: ', 'red')} Prob Enabling on all Domains at a time not Allowed.\n")
    sys.exit()

# Get the all the available domain names from the given appliance or else store the one domain name what user provides as argument.
if args.domain == "all": 
    domain_list = STATS.get_domain_names(args.appliance)
else:
    domain_list = [args.domain]

# Once domain list is ready loop it one by one to take action on prob setting
for item in domain_list:
    # Call the function to work on prob setting.
    CONFIG.set_prob(appliance=args.appliance, domain=item, object_name=args.object, action=args.probe)

    # Once prob change happens call the save config function to save the data on given domain
    CONFIG.save_config(appliance=args.appliance, domain=item)
    