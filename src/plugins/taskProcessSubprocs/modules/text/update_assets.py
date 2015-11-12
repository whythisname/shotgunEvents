import re
import shutil
import os

def main(**kwargs):
#def main(latest_workfile, new_workfile, tk, ctx):

	# Open a temp file to write to and open the file to read from
	mayafile_write = open("{0}{1}".format(kwargs['latest_workfile'], "_tmp"), "w")
	mayafile_read = open(kwargs['latest_workfile'], "r")

        output_file = ""
        for i in mayafile_read:
                output_file += i

        output_file_list = re.split(r'(;)', output_file)

	# Compile patern to match
	ref_pattern = re.compile(r'(file .*?(-rdi 1|-dr 1).*? -rfn \".*?\".*?\")(.*?)(\";)', re.DOTALL)

	# Loop through the file and replace all references with their latest versions
	for i in output_file_list:

		# Line to write, if no replacement is done we want to write it as it is
		write_to = i

		# Search line for patern
		ref_path_match = re.search(ref_pattern, i)
		# If found find the latest version of a publish and the old version
		if ref_path_match:
			# Get the matching publish template and its fields
			template_path = kwargs['tk'].template_from_path(ref_path_match.group(3))
			fields = template_path.get_fields(ref_path_match.group(3))
			# Remove the version field, this is the field we need to solve and thus don't need
			fields.pop('version')

			# Get all publishes matching a template+fields combination
			# In this case all fields need to match, except the version field
			all_versions = kwargs['tk'].paths_from_template(template_path, fields)

			# Because the versions aren't sorted we need to figure that out ourselves
			highest_version = 0
			for o in all_versions:
				curr_fields = template_path.get_fields(o)
				if curr_fields['version'] > highest_version:
					highest_version = curr_fields['version']

			# Add the version field again with the highest version number we found
			fields['version'] = highest_version
			# Apply the fields with our new version number to the template
			latest_publish = template_path.apply_fields(fields).replace("\\","/")

			# Replace the path with our new version path, it shouldn't matter if there is no new version
			#write_to = i.replace(ref_path_match.group(2), latest_publish.replace("\\","/"))
			write_to = re.sub(ref_pattern, '\g<1>{}\g<4>'.format(latest_publish), write_to)

		# Write the line to a new file
		mayafile_write.write(write_to)

	# Close all files
	mayafile_write.close()
	mayafile_read.close()

	os.rename("{0}{1}".format(kwargs['latest_workfile'], "_tmp"), kwargs['new_workfile'])
