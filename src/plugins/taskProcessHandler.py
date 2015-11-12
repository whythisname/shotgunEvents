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
        'Shotgun_Task_Change': ['sg_pre_task_execute_process', 'sg_post_task_execute_process']
    }
    
    reg.registerCallback('shotgunEventDaemon', '755d4364b9ea1b71be0ec51ccb6c219b49e91429d8cc7a4cb790763fd8dab345', taskProcessHandler, matchEvents, None)

    reg.logger.setLevel(logging.INFO)

def taskProcessHandler(sg, logger, event, args):
    """Publish a version"""

    # Break if there is no new status or if that status is not "rdy"
    if 'new_value' not in event['meta'] or event['meta']['new_value'] != 'rdy':
        return

    # Check if it's a pre or post task process that is called, I don't really see a need to separate this more than this
    pre_process = "pre" in event['attribute_name']

    # Get the process to run and break if no process is found
    filters = [["id","is",event['entity']['id']]]
    if pre_process:
        fields = ['sg_pre_task_process']
        modules = sg.find_one("Task", filters, fields)['sg_pre_task_process']
    else:
        fields = ['sg_post_task_process']
        modules = sg.find_one("Task", filters, fields)['sg_post_task_process']
    if modules is None:
        return

    # Get the paths of Published files linked to this task for pre/post processing
    # Set filter name depending on if we're processing a pre/post process
    if pre_process:
        prog_files = "task_sg_pre_task_files_tasks"
    else:
        prog_files = "task_sg_post_task_files_tasks"
    # Find the published files that link to this task and extract the paths of the files
    filters = [[prog_files, 'is', {"type": "Task", "id":event['entity']['id']}]]
    # Set fields to get, in this case just paths
    fields = ['path_cache']
    # Retrieve paths, no break is done because the operation might not need files...
    published_paths = sg.find("PublishedFile", filters, fields)

    # Process paths for subprocess
    paths_to_subproc = ""
    for i in published_paths:
        if paths_to_subproc:
            paths_to_subproc = '{} "{}"'.format(paths_to_subproc, i['path_cache'])
        else:
            paths_to_subproc = '"{}"'.format(i['path_cache'])

    # Set what we want to get: all published files belonging to this task, there should only be 1 published file (in different versions is fine)
    filters = [['task', 'is', {"type": "Task", "id":event['entity']['id']}],['published_file_type', 'is', {'type':'PublishedFileType','name':'Maya Scene','id':1}]]
    # The field to get, the path to the file
    fields = ['path', 'published_file_type']
    # Set the order in which the files are retrieved, just to make sure we get the latest version of the publish we are retrieving
    order = [{'field_name':'created_at','direction':'desc'}, {'field_name':'version_number', 'direction':'desc'}]
    # Do the request to find the publish
    task_path = sg.find_one("PublishedFile", filters, fields, order)['path']['local_path_windows']
    
    filters = [['code','is','Maya Scene']]
    fields = ['code']
    print "Maya Publish Type ID: " + str(sg.find_one("PublishedFileType", filters, fields))

    # Find the primary config of the project to find out where the config is located locally
    filters = [['code', 'is', 'Primary'], ['project', 'is', event['project']]]
    # @TODO: Load path depending on OS!
    # The paths to get from the primary config
    fields = ['windows_path']
    # Retrieve paths and break if they're not there
    project = sg.find_one("PipelineConfiguration", filters, fields)
    if project is None or project['windows_path'] is None:
        return

    if pre_process:
        script = "Pre-TaskSubproc.py"
    else:
        script = "Post-TaskSubproc.py"

    logger.info("Attemting to execute:")
    logger.info('"C:\\Python27\\python.exe" "{0}\\plugins\\taskProcessSubprocs\\{1}" "{2}" "{3}" "{4}" "{5}" {6}'.format(getScriptPath(), script, project['windows_path'], task_path, event['entity']['id'], modules, paths_to_subproc))
    subprocess.call('"C:\\Python27\\python.exe" "{0}\\plugins\\taskProcessSubprocs\\{1}" "{2}" "{3}" "{4}" "{5}" {6}'.format(getScriptPath(), script, project['windows_path'], task_path, event['entity']['id'], modules, paths_to_subproc))

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))
