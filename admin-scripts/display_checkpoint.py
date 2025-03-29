from dpmodules import Status as STATS
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

# Call the function to display list of checkpoints
STATS.get_checkpoint_list(args.appliance, args.domain)
