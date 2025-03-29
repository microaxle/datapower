import base64
import os
from jproperties import Properties
configs = Properties()

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
project_root = os.path.dirname(script_dir)

with open(f"{project_root}/dp-config.properties", 'rb') as config_file:
    configs.load(config_file)

code_base = configs.get("code_base").data
authinfo = (configs.get("user").data, base64.b64decode(configs.get("cred").data).decode("utf-8"))
secure_destination = configs.get("secure_destination").data
secure_cert = configs.get("secure_cert").data
secure_path = configs.get("secure_path").data
tmp_dir = f"{code_base}/.tmp"
domain_backup_wait_time = int(configs.get("domain_backup_wait_time").data)
checkpoint_wait_time = int(configs.get("checkpoint_wait_time").data)
domain_restore_wait_time = int(configs.get("domain_restore_wait_time").data)
api_port = int(configs.get("api_port").data)
