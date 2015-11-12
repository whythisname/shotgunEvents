"""
When a Task status is flipped to 'fin' (Final), lookup each downstream Task that is currently
'wtg' (Waiting To Start) and see if all upstream Tasks are now 'fin'. If so, flip the downstream Task
to 'rdy' (Ready To Start)

You can modify the status values in the logic to match your workflow.
"""

def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Task_Change': ['sg_status_list'],
    }
    
    reg.registerCallback('shotgunEventDaemon', '755d4364b9ea1b71be0ec51ccb6c219b49e91429d8cc7a4cb790763fd8dab345', flipDownstreamTasks, matchEvents, None)


def flipDownstreamTasks(sg, logger, event, args):
    """Flip downstream Tasks to 'rdy' if all of their upstream Tasks are 'apr'"""
    
    # we only care about Tasks that have been finalled
    if 'new_value' not in event['meta']:
        return
    if event['meta']['new_value'] == 'apr':
        
        # downtream tasks that are currently wtg
        ds_filters = [
            ['upstream_tasks', 'is', event['entity']],
            {
                "filter_operator": "any",
                "filters": [
                ['sg_status_list', 'is', 'wtg'],
                ['sg_status_list', 'is', 'hld']
                ]
            }
        ]
        fields = ['upstream_tasks']
    
        for ds_task in sg.find("Task", ds_filters, fields):
            change_status = True
            # don't change status unless *all* upstream tasks are fin
            if len(ds_task["upstream_tasks"]) > 1:
                logger.debug("Task #%d has multiple upstream Tasks", event['entity']['id'])
                us_filters = [
                    ['downstream_tasks', 'is', ds_task],
                    ['sg_status_list', 'is_not', 'apr'],
                    ]
                if len(sg.find("Task", us_filters)) > 0:
                    change_status = False
        
            if change_status:
                sg.update("Task",ds_task['id'], data={'sg_status_list' : 'rdy'})
                logger.info("Set Task #%s to 'rdy'", ds_task['id'])

    elif event['meta']['new_value'] == 'hld' or event['meta']['new_value'] == 'rdy':
        # downtream tasks that are currently not wtg
        ds_filters = [
            ['upstream_tasks', 'is', event['entity']],
            ['sg_status_list', 'is_not', 'wtg'],
            ]
        fields = ['upstream_tasks']
    
        for ds_task in sg.find("Task", ds_filters, fields):
            sg.update("Task",ds_task['id'], data={'sg_status_list' : 'hld'})
            logger.info("Set Task #%s to 'rdy'", ds_task['id'])
