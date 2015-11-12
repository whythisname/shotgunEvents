def main(**kwargs):

    code = open("C:/Program Files (x86)/ShotgunEventsServer/src/plugins/taskProcessSubprocs/modules/maya/publish_code.py","r")
    output_file = r""
    for i in code:
        output_file += i
        output_file += "\n"
    code.close()
    
    kwargs['main_app'].stdin.write(output_file)

    return
