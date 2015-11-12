import subprocess
#subprocess.call("//MINIVEGASDC/projects/Shotgun_software/2015/15_016_asus_ar_app_clone/tank.bat maya_2015")

maya = subprocess.Popen("//MINIVEGASDC/projects/Shotgun_software/2015/15_016_asus_ar_app_clone/tank.bat maya_2015", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def launchMaya(mayaInstance):
	mayaInstance.stdin.write('import maya.standalone\n\
maya.standalone.initialize(name="python")\n\
import maya.cmds as cmds\n\
import maya.mel as mel\n')

launchMaya(maya)

maya.stdin.write('mel.eval(\'source mv_SubmitPlayblastToDeadline;\\nmvSubmitPlayblastToDeadline;\')\n')

#print out
#print err

out, err = maya.communicate('import sgtk\n\
print sgtk.platform.current_engine().context.project')

print out
print err

exitcode = maya.returncode

print exitcode