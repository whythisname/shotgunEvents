import sys
import glob
import os
import shutil

def publishingSubProc(winpath, vpath, vcode, eventID, linkType, linkID, taskID):

    # Get toolkit engine (sgtk) of the project
    sys.path.append('%s/install/core/python' % winpath)
    import sgtk
    sys.path.remove('%s/install/core/python' % winpath)
    #f, filename, desc = imp.find_module('sgtk', ['%s/install/core/python/' % winpath])
    #sgtk = imp.load_module('sgtk', f, filename, desc)

    
    # Publish the version
    # Get toolkit
    tk = sgtk.sgtk_from_path(vpath)
    tk.synchronize_filesystem_structure()
    # Set context
    ctx = tk.context_from_entity(linkType,linkID)
    #print(ctx)

    # Construct path to facilis, this is where the renders have to be copied to and needs to be put in the publish
    # Get the template to the rendered frames
    version_path_template = tk.templates['maya_render_shot_version']
    # Get field data from vpath with the use of the template
    fields = version_path_template.get_fields(vpath.replace("\\","/"))
    # Get the template location of where to copy the frames to
    publish_path_template = tk.templates['maya_render_shot_publish']
    # Apply the field data to the "publish" template and remove the file name because we only need the destination directory for copying purposes
    facilis_dir_path = publish_path_template.parent.apply_fields(fields)
    # Apply the field data to the entire template as well, for publishing after the file copying
    publish_location = publish_path_template.apply_fields(fields)
    
    # Check if path to copy to exists, if not -> create it
    # @TODO: what if the folder exists and has files in it, overwrite? abort?
    if not os.path.exists(facilis_dir_path):
        os.makedirs(facilis_dir_path)

    # Start copy and rename loop
    for frame in glob.glob(vpath.replace("#", "?")):
        # First, copy the file to the new destination, this is the easy part
        #print(frame)
        #print(facilis_dir_path)
        shutil.copy(frame, facilis_dir_path)

        # Second, rename the file to fit the publish template
        # To do that first we get the name of the file we just copied and append it to the path we copied to.
        # That way we get the complete path + file name so we know what to rename and where it is located
        old_file = os.path.split(frame)[1]
        rename_from_file = os.path.join(facilis_dir_path, old_file)
        
        # Next get the fields from the version template, this is done here because only now the file has the frame number in its name
        # Unlike before where it was just ####
        fields = version_path_template.get_fields(frame)
        # Apply the fields to the publishing template to figure out to what to rename the file
        rename_to_file = publish_path_template.apply_fields(fields)
        # Do the actual renaming if the file names don't match
        if rename_from_file != rename_to_file:
            os.rename(rename_from_file, rename_to_file)
    
    # Register the publish
    published_entity = sgtk.util.register_publish(tk, ctx, publish_location, vcode, fields['version'], published_file_type='Rendered Image', version_entity={"type":"Version", "id":eventID}, task={"type":"Task", "id":taskID})
    return published_entity
    # Remove the location of sgtk so we can reload the sgtk from a different project... hopefully
    #sys.path.remove('%s/install/core/python' % winpath)

published_entity = publishingSubProc(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], int(sys.argv[6]), int(sys.argv[7]))
unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
unbuffered.write(str(published_entity['id']))

#publishingSubProc("//minivegasdc/projects/Shotgun_software/_ctm_14_079ctmpicturesidentdesign", "//minivegasdc/projects/Shotgun_Projects/_ctm_14_079ctmpicturesidentdesign/sequences/sequence_01/CTM_S040/Light/work/maya/images/DeadlineTest.v004/masterLayer/DeadlineTest.v004.####.exr", "TestRender")
