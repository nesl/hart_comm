#!/usr/bin/env python

import subprocess
import threading
import os
import signal
import pwd
import sys
import time


class Command(object):
    def __init__(self, args):
        #self.cmd = ' '.join(['./student_bin'] + args)
        self.cmd = './student_bin %s > stdout.txt 2> stderr.txt' % (
                ' '.join(args))
        self.args = args
        self.process = None

    def run(self, timeout):
        def target():
            print 'Thread started'
            self.process = subprocess.Popen(self.cmd, shell=True, preexec_fn=os.setsid)
            self.process.communicate()
            print 'Thread finished'

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            print 'Terminating process'

            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
                print('send sigint')
            except:
                pass

            time.sleep(3)

            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                print('send sigterm')
            except:
                pass

            time.sleep(3)

            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                print('send sigkill')
            except:
                pass
            thread.join()

        print self.process.returncode

        file_check_list = self.args + ['stdout.txt', 'stderr.txt']
        for file_name in file_check_list:
            if not os.path.isfile(file_name):
                with open(file_name, 'w') as fo:
                    fo.write('Error: Your program did not generate this file. This is auto-generated.')


# set working directory to student folder

print(os.getcwd())
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
student_folder = os.path.join(dname, 'files')
os.chdir(student_folder)

os.chmod('student_bin', 0777)

#uid = pwd.getpwnam('student')[2]
#os.setuid(uid)

print(os.getcwd())

args = sys.argv[1:]
command = Command(args)

command.run(timeout=30)

