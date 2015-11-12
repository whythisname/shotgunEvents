import sys
import glob
import os
import shutil
import inspect
import imp

import re

def getScriptPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def preTaskProc(winpath, task_path, task_id, procmodules, **kwargs):

    """
    This procedure handles any batch processing of files in or before a task.

    Input:
    
    winpath: Path to sgtk of the project
    task_path: Path to set context to
    procmodules: string of modules to use to process the file with
    **kwargs: any additional files to process with the modules

    winpath is temporarily appended to the syspath in order to import the right sgtk.
    task_path is used to find the most recent work file. This means it doesn't matter what version of a publish is given.
    In order to convert from a publish path to a work file path the template name is expected to have a 
    """

    # Get toolkit engine (sgtk) of the project
    sys.path.append('%s/install/core/python' % winpath)
    import sgtk
    sys.path.remove('%s/install/core/python' % winpath)
    
    # Get toolkit
    tk = sgtk.sgtk_from_path(task_path)
    # Sync file system if core version is greater than v0.15.xx, because this function didn't exsist before and will cause errors otherwise
    # It is mandatory for any release after v0.15.xx though
    tkv = tk.version.replace("v","").split(".")
    if int(tkv[0]) > 0 or int(tkv[1]) >= 15:
        tk.synchronize_filesystem_structure()
    else:
        pass
    # Set context
    ctx = tk.context_from_path(task_path)

    # Construct path to next task work area, this is where the renders have to be copied to and needs to be put in the publish
    # Get the template of the publish
    publish_path_template = tk.template_from_path(task_path)
    # Get field data from task_path with the use of the template
    fields = publish_path_template.get_fields(task_path)
    #fields['Step'] = 'Light' # TODO: Next step

    # Get work template of the publish, this assumes the templates have the same name except with the "publish" part being replaced by "work"
    work_path_template = tk.templates[publish_path_template.name.replace("publish","work")]

    # We want the latest work file of the publish    
    # Remove the version field, this is the field we need to solve and thus don't need
    fields.pop('version')

    # Get all publishes matching a template+fields combination
    # In this case all fields need to match, except the version field
    all_versions = tk.paths_from_template(work_path_template, fields)

    # Because the versions aren't sorted we need to figure that out ourselves
    highest_version = 0
    for o in all_versions:
        curr_fields = work_path_template.get_fields(o)
        if curr_fields['version'] > highest_version:
            highest_version = curr_fields['version']

    # Add the version field again with the highest version number we found
    fields['version'] = highest_version
    # Apply the fields with our new version number to the template
    latest_workfile = work_path_template.apply_fields(fields)

    print latest_workfile

    testctx = tk.context_from_path(latest_workfile)

    # Check if path to copy to exists, if not -> create it
   # if not os.path.exists(work_dir_path):
   #     os.makedirs(work_dir_path)

    # Split modules string into separate parts to get different modules
    modules = str(procmodules).split(", ")

    # Get application and version to set environment variables
#    setAppEnv(modules[0], 2014)
#    app = modules[0]
    # Remove the application from the modules list
#    modules.pop(0)

    # Put all functions in the module into a list
#    module_functions = ""
    for i in range(len(modules)):
        modules[i] = modules[i].replace(" ", "_")

#        module = "{0}.py".format(module)
#        module_func = open("{0}/modules/{1}/{2}".format(getScriptPath(), app, module), "r")
#        for o in module_func:
#            module_functions = "{0}{1}".format(module_functions, o)
#        module_func.close()

     # use this if you want to include modules from a subfolder
    
    # First import the module root
    mod_root_location = imp.find_module("modules")
    mod_root = imp.load_module("modules", mod_root_location[0], mod_root_location[1], mod_root_location[2])

    # Pop and import the main module, this is the module all functions after it should be in
    main_mod = modules.pop(0)
    mod_main_location = imp.find_module(main_mod, mod_root.__path__)
    mod_main = imp.load_module(main_mod, mod_main_location[0], mod_main_location[1], mod_main_location[2])

    # Create a path to a new version for use after any potential publishing
    fields['version'] = fields['version'] + 1
    new_workfile = work_path_template.apply_fields(fields)
    # Create a dictionary with all arguments needed for all scripts, not the most efficient but this allows easy iteration over all modules
    script_args = {
    "sgtk" : sgtk,
    "tk" : tk,
    "ctx" : ctx,
    "task_id" : task_id,
    "fields" : fields,
    "publish_path_template" : publish_path_template,
    "new_workfile" : new_workfile,
    "work_path_template" : work_path_template,
    "latest_workfile" : latest_workfile.replace("\\","/")
    }

    # If the main module is the module of an application it should be launched as "main_app" and should therefore exist
    # If it does exist add it to the dictionary so you can use it in the modules
    if hasattr(mod_main,'launchMainApp'):
        print winpath
        print script_args['latest_workfile']
        script_args['main_app'] = mod_main.launchMainApp(winpath.replace("\\","/"), "mayapy_2015", script_args['latest_workfile'])
        #script_args['main_app'] = mod_main.launchMainApp("//MINIVEGASDC/projects/Shotgun_software/2015/15_xxx_symlinktestproject", "mayapy_2015", "//minivegasdc/projects/2015/15_xxx_symlinktestproject/post_production/sequences/clickclick/BAM-/Exp/work/maya/testScene.v010.ma")
        print script_args['main_app']
        #script_args['main_app'] = mod_main.main_app

    # Import and run every module in the modules list, not the most efficient way to execute but easiest to iterate on for a modular system
    for i in modules:
        mod_sub_location = imp.find_module(i, mod_main.__path__)
        mod_sub = imp.load_module(i, mod_sub_location[0], mod_sub_location[1], mod_sub_location[2])
        mod_sub.main(**script_args)

    if hasattr(mod_main,'launchMainApp'):
        out, err = script_args['main_app'].communicate('print "close"')
        exitcode = script_args['main_app'].returncode

        print out
        print err
        print exitcode


    #cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"modules/text")))
    #if cmd_subfolder not in sys.path:
    #    sys.path.insert(0, cmd_subfolder)

    # We should save our changes in a new version instead of over writing our old file
    # So add 1 to the version and fill in the template again to get our new version path
#    fields['version'] = fields['version'] + 1
#    new_workfile = work_path_template.apply_fields(fields)
#
#    import update_assets
#    update_assets.main(latest_workfile.replace("\\","/"), new_workfile, tk, ctx)

    # Insert any variables in the script that it might need
#    formats = re.findall(r"\{.*\}", module_functions)
#    for i in formats:
#        if i == "{task_path}":
#            module_functions = module_functions.replace(i, task_path.replace("\\","/"))

#    import publish
#    publish.main(sgtk, tk, ctx, task_id, fields, publish_path_template, new_workfile, work_path_template)    

    # 


    return

    # Modules to run
    base_script = '{modules}\n\
    file -rename "{output_file_name}";\n\
    file -save -type "mayaAscii";\n\
    quit;'

    base_script.format(modules=module_functions)


    
    # Temp folder to store the script to execute
    tempdir = "C:/deadlineSubmitTemp/"
    # Create temp dir if it doesn't exist
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    
    # Files to open, import and output
    open_scene = "//MINIVEGASDC/projects/2015/14_100_BoseInteractiveAnimationfilm/post_production/sequences/RenderSeq/RenderScene/Light/work/maya/testLightSetupStage.v001.ma"
    #output_scene = "//minivegasdc/projects/2015/14_100_BoseInteractiveAnimationfilm/post_production/sequences/RenderSeq/RenderScene/Light/work/maya/DeadlineMergeTest.v001.ma"
    #import_scene = "C:/Users/localadmin/Desktop/AlembicExports/extra_attribs.abc"
    #open_scene = sys.argv[1]
    
    import_scenes = ["C:/Users/localadmin/Desktop/AlembicExports/extra_attribs.abc","C:/Users/localadmin/Desktop/AlembicExports/extra_attribs.abc","C:/Users/localadmin/Desktop/AlembicExports/extra_attribs.abc","C:/Users/localadmin/Desktop/AlembicExports/extra_attribs.abc"]
    
    for mergeme in range(2, len(import_scenes)-1):
    
        output_scene = os.path.split(mergeme)[1]
        output_scene = output_scene[:output_scene.rfind(".")]
    
        tempmel = open("{0}temp.mel".format(tempdir), "w")
        script = base_script.format(file_name = import_scenes[mergeme], output_file_name = output_scene)
        tempmel.write(script)
        tempmel.close()
    
        os.system('C:/Program^ Files/Autodesk/Maya2014/bin/mayabatch.exe -prompt -file "{0}" -command "source "\^\"{1}\^\";"'.format(open_scene, "{0}temp.mel".format(tempdir)))
    
    return

    # Start copy and rename loop
    for frame in glob.glob(task_path.replace("#", "?")):
        # First, copy the file to the new destination, this is the easy part
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
        rename_to_file = work_path_template.apply_fields(fields)
        # Do the actual renaming if the file names don't match
        if rename_from_file != rename_to_file:
            os.rename(rename_from_file, rename_to_file)
    
    # Register the publish
    #sgtk.util.register_publish(tk, ctx, publish_location, vcode, 2, published_file_type='Rendered Image')

def setAppEnv(application, app_version):
    if application == "maya":

        # Load Maya environment variables
        envfile = open("//MINIVEGASDCBU/App_configs/MayaResources/maya{0}/Maya.env".format(str(app_version)), "r")
        for line in envfile:
            linestrip = line.strip().replace(" ","")
            keyvar = linestrip.split("=")
            if len(keyvar) == 2:
                try:
                    curvar = os.environ["{0}".format(keyvar[0])]
                except:
                    os.environ["{0}".format(keyvar[0])] = str(keyvar[1])
                    continue
                os.environ["{0}".format(keyvar[0])] = "{0};{1}".format(curvar, str(keyvar[1]))
        envfile.close()

    elif application == "text":
        pass


preTaskProc(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])

# TODO: Put sys.argv[5] to sys.argv[len(sys.argv)] in dict for **kwargs

#preTaskProc("//minivegasdc/projects/Shotgun_software/2015/14_100_BoseInteractiveAnimationfilm", "//MINIVEGASDC/projects/2015/14_100_BoseInteractiveAnimationfilm/post_production/sequences/testSeq/mergeTestShot/Anm/publish/maya/mergeIntoScene.v003.ma", 3166, "text, update assets, publish", kwargs="")
