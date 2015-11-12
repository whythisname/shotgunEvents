"""
Automatically calculate the Cut Duration on Shots when the Cut In or Cut Out value is changed.

Conversely, this example does not make any updates to Cut In or Cut Out values if the Cut Duration field 
is modified. You can modify that logic and/or the field names to match your specific workflow.
"""

import logging
import sys
import os
import subprocess


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['sg_status_list'],
    }
    
    reg.registerCallback('shotgunEventDaemon', '755d4364b9ea1b71be0ec51ccb6c219b49e91429d8cc7a4cb790763fd8dab345', versionToPublish, matchEvents, None)

    reg.logger.setLevel(logging.INFO)

def versionToPublish(sg, logger, event, args):
    """Publish a version"""

    # Break if there is no new status or if that status is not "apr"
    if 'new_value' not in event['meta'] or event['meta']['new_value'] != 'apr':
        return
    
    # Find the version entity to be published and extract the information we need
    filters = [['id', 'is', event['entity']['id']]]
    # Information to be extracted
    fields = ['description', 'entity', 'sg_path_to_frames', 'sg_task', 'code']#, 'image']
    # Retrieve info and break if it's not present
    version = sg.find_one("Version", filters, fields)
    if version is None:
        return

    print version

    # Find the primary config of the project to find out where the config is located locally
    filters = [['code', 'is', 'Primary'], ['project', 'is', event['project']]]
    # @TODO: Load path depending on OS!
    # The paths to get from the primary config
    fields = ['windows_path']
    # Retrieve paths and break if they're not there
    project = sg.find_one("PipelineConfiguration", filters, fields)
    if project is None or project['windows_path'] is None:
        return

    try:
        publish_ID = subprocess.call('"C:\\Python27\\python.exe" "C:\\Program Files (x86)\\ShotgunEventsServer\\src\\plugins\\versionToPublishSubproc\\subproc.py" "%s" "%s" "%s" "%s" "%s" "%s" "%s"' % (project['windows_path'], version['sg_path_to_frames'], version['code'], event['entity']['id'], version['entity']['type'], version['entity']['id'], version['sg_task']['id']))
        print publish_ID
        logger.info("Published event: {} to {}".format(event['entity']['id'],publish_ID))
    except:
        logger.info("Publish event: {} Failed!".format(event['entity']['id']))
        

    # Set what we want to get: all published files belonging to this task, there should only be 1 published file (in different versions is fine)
    #filters = [['task', 'is', {"type": "Task", "id":event['entity']['id']}]]
    # The field to get, the path to the file
    #fields = ['id']
    # Set the order in which the files are retrieved, just to make sure we get the latest version of the publish we are retrieving
    #order = [{'field_name':'version_number', 'direction':'desc'}]
    # Do the request to find the publish
    # publish_ID = sg.find_one("PublishedFile", fields, order)
    
    #print version['published_files']
    
    #sg.update("PublishedVersion",publish_ID,{"image":version["image"]})

    #logger.info("Attempted to publish: %s" % event['entity']['id'])
