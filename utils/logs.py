def make_print_to_file(path='./log/', write_type = 'a', file_name = None):
    '''
    path,  it is a path for save your log about fuction print
    example:
    use  make_print_to_file() and the all the information of funtion print , will be write in to a log file
    :return:
    '''
    import datetime
    import os
    import sys

    if not os.path.exists(path):
        os.makedirs(path)
 
    class Logger(object):
        def __init__(self, filename="Default.log", path="./"):
            self.terminal = sys.stdout
            self.log = open(os.path.join(path, filename), write_type, encoding='utf8',)
            # out.flash
 
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message) ; self.log.flush()
 
        def flush(self):
            pass
            
    if file_name is None:

        fileName = datetime.datetime.now().strftime('day'+'%Y_%m_%d')
    else:
        fileName = file_name
 
    try:
        sys.stdout = Logger(fileName + '.log', path=path)
    except:
        sys.stdout = Logger(fileName + '/.log', path=path)

    #############################################################
    # 这里输出之后的所有的输出的print 内容即将写入日志
    #############################################################
    print(fileName.center(60,'*'))
