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
parser.add_argument("-o", "--object_name", help="WSP service name or provide 'all' - It is Required Argument", required=True)
parser.add_argument("-s", "--sort", help="sort with table header values - default sort is 'ProbStatus'", default="ProbStatus")

# parse and store all the user arguments into 'args' variable
args = parser.parse_args()

STATS.get_wsp(appliance=args.appliance, domain=args.domain, object_name=args.object_name, sort_option=args.sort)
    
