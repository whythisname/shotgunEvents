"""
Initializes Maya for use in the module

Output:
maya.main_app = Popen with a running Maya instance.

WARNING: This script only launches Maya, so the closing of it must be handled in another script! 
"""

import subprocess

def launchMainApp(projectPath, application, openFile):

	print "projectPath: " + projectPath
	print "application: " + application
	print "openFile: " + openFile

	main_app = subprocess.Popen("{0}/tank.bat {1}".format(projectPath, application), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	main_app.stdin.write('import maya.standalone\n\
maya.standalone.initialize(name="python")\n\
import maya.cmds as cmds\n\
import maya.mel as mel\n\
import sgtk\n\
cmds.file("{0}", open=True)\n'.format(openFile))
	print main_app
	return main_app


#main_app = launchMainApp("//MINIVEGASDC/projects/Shotgun_software/2015/15_016_asus_ar_app", "mayapy_2015", "//minivegasdc/projects/2015/15_016_asus_ar_app/post_production/sequences/test_seq/test_export_unity/Anm/work/maya/testBirdy.v006.ma")
#out, err = main_app.communicate('print "close"')
#exitcode = main_app.returncode

#print out
#print err
#print exitcode
