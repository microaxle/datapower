from dpmodules import FileManagement as FM
from dpmodules import ini as ini
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
parser.add_argument("-p", "--targetpath", help="Datapower directory path to upload. Give full path - Example 'local/subdirectory/filename'", required=True)
parser.add_argument("-f", "--filepath", help="full path of the file which you want to deploy Example - '/home/user/code/file1'", required=True)
parser.add_argument("-o", "--overwrite", help="on this flag if you want to overwrite the file- Default is 'off'", default="off")


# parse and store all the user arguments into 'args' variable
args = parser.parse_args()

# Call the function to deploy given file
FM.deploy_file(args.appliance, args.domain, args.targetpath, args.filepath, args.overwrite)
