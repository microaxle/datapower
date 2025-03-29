from dpmodules import FileManagement as FM

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
parser.add_argument("-b", "--basefolder", help="Base folder where you want to create custom dir", required=True)
#parser.add_argument("-f", "--folder", help="Give folder name - Example 'local/myfolder'", required=True)


# parse and store all the user arguments into 'args' variable
args = parser.parse_args()

# Call the function to create dir on given location
FM.create_dir(args.appliance, args.domain, args.basefolder)
