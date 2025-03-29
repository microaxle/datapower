from dpmodules import ImportExport as IE
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
parser.add_argument("-t", "--testrun", help="DryRun on/off ? - default is 'off'", default='off')
args = parser.parse_args()

# call the function to restore the domain.
# If the domain is presented, it sync with the backup. if domain not presented already, 
# script will create domain automatically based on content inside the backup zip we provide.

IE.restore_domain(appliance=args.appliance, domain=args.domain, zip_file=args.zipfile, DryRun=args.testrun)
