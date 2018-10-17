import json
import sys
import subprocess
import os

extensionID=os.environ['extensionID']
clientID=os.environ['clientID']
clientSecret=os.environ['clientSecret']
refreshTok=os.environ['refreshTok']

def update_version():
    manifest = json.loads(open('webextension/manifest.json').read())
    
    curr_version = manifest['version'].split('.')
    new_version = curr_version[0] + '.' + curr_version[1] + '.' + str(int(curr_version[2]) + 1)
    
    manifest['version'] = new_version
    
    with open('webextension/manifest.json', 'w') as outfile:
        json.dump(manifest, outfile)

    return new_version

def execute():
    command='webstore upload --source=webextension/ \
                         --extension-id=' + extensionID + ' \
                         --client-id=' + clientID + ' \
                         --client-secret=' + clientSecret + ' \
                         --refresh-token=' + refreshTok + ' \
                         --auto-publish' 

    subprocess.check_output(command, shell=True)

if __name__ == "__main__":
    new_version = update_version()
    print('Attempting to publish with version: ' + new_version)
    execute()



