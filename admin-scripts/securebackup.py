# This program takes appliance as argument and do secure backup of it. 
# The location where it needs to save the backup file, should come from properties file.
# The directory structure will be created automatically bases on applicance/domain/object etc.

from dpmodules import ImportExport as IE
import argparse
parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Default, Mandatary and optional arguments while calling the program
parser.add_argument("-a", "--appliance", help="Datapower Host - It is Required Argument", required=True)

# parse and store all the user arguments into 'args' variable
args = parser.parse_args()

# call the secure backup function
IE.secure_backup(args.appliance)
