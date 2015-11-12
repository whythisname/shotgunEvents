import os
import shutil

def main(**kwargs):
#def main(sgtk, tk, ctx, task_id, fields, publish_path_template, new_workfile, work_path_template):

	"""
	This module publishes the latest version of an already published file and version ups the file.
	
	Flow: Take published file -> find latest non-published version (work file) of that file -> 
	publish latest work file -> version up latest work file

	Expected dict of kwargs:

	sgtk: Shotgun sgtk object 
	tk: Shotgun toolkit instance
	ctx: Shotgun context 
	task_id: ID of task on Shotgun website 
	fields: fields to fill in work/publish file templates 
	publish_path_template: Template of the published file, so we know where to put our new publish when we fill it in with the fields 
	new_workfile: A path to use for the version up after publishing 
	work_path_template: Template of the work file

	"""

	# Path to published files
	publish_path = kwargs['publish_path_template'].apply_fields(kwargs['fields'])

	# Publishing folder
	publish_folder = kwargs['publish_path_template'].parent.apply_fields(kwargs['fields'])

	# Make sure folder to publish to exists, it should but let's make sure
	if not os.path.exists(publish_folder):
		os.makedirs(publish_folder)

	# Version to publish
	version_number = kwargs['fields']['version']

	version_name = kwargs['fields']['name']

	# Publishing file type, abort if the extension doesn't match anything
	extension = os.path.splitext(publish_path)[1]
	if extension == ".ma":
		file_type = "Maya Scene"
	elif extension == ".nk":
		file_type = "Nuke Script"
	else:
		print("Error: Unkown file type for publishing! Aborting publish!")
		return

	# Copy file to publish folder and rename it
	shutil.copy(kwargs['new_workfile'], publish_path)

	# Register publish on Shotgun
	kwargs['sgtk'].util.register_publish(kwargs['tk'], kwargs['ctx'], publish_path, version_name, version_number, published_file_type=file_type, task={"type":"Task", "id":kwargs['task_id']})

	# Copy and increment work file so we keep the same "version->publish->version up" flow all other publishes have
	kwargs['fields']['version'] = kwargs['fields']['version'] + 1
	version_up = kwargs['work_path_template'].apply_fields(kwargs['fields'])
	shutil.copy(kwargs['new_workfile'], version_up)