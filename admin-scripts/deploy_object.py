from dpmodules import ImportExport as IE
from dpmodules import Status as STATS
import argparse

parser = argparse.ArgumentParser()

# It ignore python warnings which helps to ignore tls signer authentication
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")

# Default, Mandatary and optional arguments while calling the program
parser.add_argument("-a", "--appliance", help="Datapower Host", required=True)
parser.add_argument("-d", "--domain", help="Datapower Application Domain", required=True)
parser.add_argument("-z", "--zipfile", help="Zip file location", required=True)
parser.add_argument("-o", "--OverwriteObjects", help="OverwriteObjects? 'on/off' - default is 'off'", default="off")
parser.add_argument("-f", "--OverwriteFiles", help="OverwriteFiles? 'on/off' - default is 'off'", default="off")
parser.add_argument("-t", "--DryRun", help="DryRun - default is 'off'", default="off")
args = parser.parse_args()

# Call the function to deploy the given object zip file
IE.deploy_object(args.appliance, args.domain, args.zipfile, args.OverwriteObjects, args.OverwriteFiles, args.DryRun)
