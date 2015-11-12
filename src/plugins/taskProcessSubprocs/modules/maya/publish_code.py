import sgtk

class PublishData():
    
    def __init__(self, tasks, shotgun_task):
        self._shotgun_task_list = tasks
        self._shotgun_task = shotgun_task
    
    @property
    def selected_tasks(self):
        return self._shotgun_task_list
    
    @property
    def shotgun_task(self):
        return self._shotgun_task
    
    @property
    def thumbnail(self):
        return None
    
    @property
    def comment(self):
        return "Automated Publish."

class TaskProgressReporter():
    
    def __init__(self, stage_count=1):
        return
    
    def reset(self, arg=None):
        return 0
  
    def report(self, percent=0, msg=None, stage=None):
        pass

test = sgtk.platform.current_engine().apps['tk-multi-publish'].import_module("tk_multi_publish")
class PublishHandlerNoUi(test.PublishHandler):
    def no_ui_publish(self, publish_form):
        """
        Slot called when publish signal is emitted from the UI
        """

        from tank import TankError
        
        # get list of tasks from UI:
        selected_tasks = publish_form.selected_tasks

        # stop if can't actually do the publish!
        if not selected_tasks:
            # TODO - replace with tank dialog
            print("Nothing selected to publish - unable to continue!")
            return
            
        # split tasks into primary and secondary:
        primary_task=None
        secondary_tasks=[]
        for ti, task in enumerate(selected_tasks):
            if vars(task.output) == vars(self._primary_output):
                if primary_task:
                    raise TankError("Found multiple primary tasks to publish!")
                primary_task = task
                secondary_tasks = selected_tasks[:ti] + selected_tasks[(ti+1):]
        if not primary_task:
            raise TankError("Couldn't find primary task to publish!")
            
        # pull rest of info from UI
        sg_task = publish_form.shotgun_task
        thumbnail = publish_form.thumbnail
        comment = publish_form.comment
        
        # create progress reporter and connect to UI:
        progress = TaskProgressReporter(selected_tasks)
        print(progress)

        # show pre-publish progress:
        print("Doing Pre-Publish")
        progress.reset()
        
        # make dialog modal whilst we're doing work:
        """
        (AD) - whilst this almost works, returning from modal state seems to
        completely mess up the window parenting in Maya so may need to have another
        way to do this or (more likely) move it to a separate dialog!
        
        geom = publish_form.window().geometry() 
        publish_form.window().setWindowModality(QtCore.Qt.ApplicationModal)
        publish_form.window().hide()
        publish_form.window().show()
        publish_form.window().setGeometry(geom)
        """
                    
        # do pre-publish:
        try:
            self._do_pre_publish(primary_task, secondary_tasks, progress.report)
        except TankError, e:
            print("Pre-Publish Failed!\n%s" % e)
            return
        except Exception, e:
            self._app.log_exception("Pre-publish Failed")
            return
        finally:
            pass
        
        # check that we can continue:
        num_errors = 0
        for task in selected_tasks:
            num_errors += len(task.pre_publish_errors)
        if num_errors > 0:
            
            print "Pre-Publish errors!"
            return
                
        # show publish progress:
        print("Publishing")
        progress.reset()

        # save the thumbnail to a temporary location:
        thumbnail_path = ""
        try:
            if thumbnail and not thumbnail.isNull():
                # have a thumbnail so save it to a temporary file:
                temp_file, thumbnail_path = tempfile.mkstemp(suffix=".png", prefix="tanktmp")
                if temp_file:
                    os.close(temp_file)
                thumbnail.save(thumbnail_path)
                    
            # do the publish
            publish_errors = []
            do_post_publish = False
            try:            
                # do primary publish:
                primary_path = self._do_primary_publish(primary_task, sg_task, thumbnail_path, comment, progress.report)
                do_post_publish = True
                
                # do secondary publishes:
                self._do_secondary_publish(secondary_tasks, primary_task, primary_path, sg_task, thumbnail_path, 
                                           comment, progress.report)
                
            except TankError, e:
                self._app.log_exception("Publish Failed")
                publish_errors.append("%s" % e)
            except Exception, e:
                self._app.log_exception("Publish Failed")
                publish_errors.append("%s" % e)
        finally:
            # delete temporary thumbnail file:
            if thumbnail_path:
                os.remove(thumbnail_path)
        
        # check for any other publish errors:
        for task in secondary_tasks:
            for error in task.publish_errors:
                publish_errors.append("%s, %s: %s" % (task.output.display_name, task.item.name, error))
        
        # if publish didn't fail then do post publish:
        if do_post_publish:
            print("Doing Post-Publish")
            progress.reset(1)
            
            try:
                self._do_post_publish(primary_task, secondary_tasks, progress.report)
            except TankError, e:
                self._app.log_exception("Post-publish Failed")
                publish_errors.append("Post-publish: %s" % e)
            except Exception, e:
                self._app.log_exception("Post-publish Failed")
                publish_errors.append("Post-publish: %s" % e)
        else:
            # inform that post-publish didn't run
            publish_errors.append("Post-publish was not run due to previous errors!")
            
        # show publish result:
        print(not publish_errors) 
        print(publish_errors)
 
no_ui_publish_class = PublishHandlerNoUi(sgtk.platform.current_engine().apps['tk-multi-publish'])

exportItems = ['Deformation','T100HA']
tasks_to_publish = []
for i in no_ui_publish_class.get_publish_tasks():
    print i.item.raw_fields
    if 'work_file' == i.item.raw_fields['type']:
        tasks_to_publish.append(i)
    elif 'anim_rig' == i.item.raw_fields['type'] and [True for x in exportItems if x.lower() in i.item.raw_fields['name'].lower()]:
        tasks_to_publish.append(i)

shotgun_task = no_ui_publish_class.get_shotgun_tasks()[0]
publish_data = PublishData(tasks=tasks_to_publish, shotgun_task=shotgun_task)

no_ui_publish_class = PublishHandlerNoUi(sgtk.platform.current_engine().apps['tk-multi-publish'])
no_ui_publish_class.no_ui_publish(publish_data)
