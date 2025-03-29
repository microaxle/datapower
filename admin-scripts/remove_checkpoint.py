from dpmodules import Config as CONFIG
import argparse
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Default, Mandatary and optional arguments while calling the program
parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True)
parser.add_argument("-d", "--domain", help="Datapower Application Domain or 'all' - It is Required Argument", required=True)


# parse and store all the user arguments into 'args' variable
args = parser.parse_args()
# 

# Call the function to delete check point from given domain
CONFIG.delete_checkpoint(args.appliance, args.domain)
