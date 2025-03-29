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
parser.add_argument("-p", "--dirpath", help="Datapower directory to download. Give full path if it is sub dir - Example 'local/subdirectory'", required=True)


# parse and store all the user arguments into 'args' variable
args = parser.parse_args()

# Call the function to take backup of given dir
FM.backup_dir(args.appliance, args.domain, args.dirpath)
