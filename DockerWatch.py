import argparse
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FullPath(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))

parser = argparse.ArgumentParser(description='A program that mirrors files between a docker container and a local directory.\
                                             the program assumes that you have initially copied all the files to the docker container.\
                                             It will only mirror the local files to the docker container not the other way around!',
                                 epilog='Example: python3 DockerWatch.py --source /usr/workdir --dest container_id:/usr/workdir')

parser.add_argument('-s', '--source', help='Source directory to watch',
                    required=True, metavar='FILE', action=FullPath)

parser.add_argument('-d', '--dest', help='Destination directory to link files to',
                    required=True)

parser.add_argument('-r', '--recursive', help='Search recursively in subfolders (default is 1 - true)',
                    required=False, action='store_true', default=1)

args = parser.parse_args()

if not args.source:
    print('You need to provide a source directory! Use --source')
    exit(1)

if not args.dest:
    print('You need to provide a destination directory! Use --dest')
    exit(1)

class Watcher:
    def __init__(self, filepath, recursive=True):
        self.path = filepath
        self.observer = Observer()
        self.recursive = recursive
    
    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path, recursive=self.recursive)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
            print('Exiting gracefully...')
        except:
            self.observer.stop()
            print ('Error. Something went wrong. Oops!')
        self.observer.join()

def get_container_name(dest_path):
    rv = ''
    for i in range(0, len(dest_path)):
        if(dest_path[i]==':'):
            break
        rv += dest_path[i]
    return rv

def get_container_dir(dest_path):
    rv = ''
    for i in range(0, len(dest_path)):
        if(dest_path[i]==':'):
            rv = dest_path[i+1:]
            break
    return rv

def run_command(command, who):
    tmp = subprocess.Popen(command, stdout=subprocess.PIPE)
    output = tmp.communicate()[0]    
    if True:
        print(who + ' says:')
        print(output)        

def send_file(src_path):
    run_command(["docker","cp", src_path, args.dest + '/' + os.path.relpath(src_path)], 'Docker')

def delete_file(src_path):
    container_name = get_container_name(args.dest)
    run_command(["docker", "exec", container_name, "rm", "-rf", '/' + os.path.relpath(src_path)], 'Docker')

def create_directory(src_path):
    container_name = get_container_name(args.dest)
    run_command(["docker", "exec", container_name, "mkdir", "-p", '/' + os.path.relpath(src_path)], 'Docker')

def delete_directory(src_path):
    container_name = get_container_name(args.dest)
    run_command(["docker", "exec", container_name, "rm", "-rf", '/' + os.path.relpath(src_path)], 'Docker')

def rebase():
    container_name = get_container_name(args.dest)
    run_command(["docker", "exec", container_name, "rm", "-rf", get_container_dir(args.dest)], 'Docker')
    run_command(["docker", "exec", container_name, "mkdir", "-p", args.dest], 'Docker')
    run_command(["docker", "cp", args.source + '/.', args.dest], 'Docker')

class Handler(FileSystemEventHandler): 

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            if event.event_type == 'created':
                create_directory(event.src_path)
                print('Created Folder')
            elif event.event_type == 'deleted':
                delete_directory(event.src_path)
                print('Deleted Folder')
        elif event.event_type == 'created':
            send_file(event.src_path)
            print ('Received created event - %s.' % event.src_path)
        elif event.event_type == 'modified':
            send_file(event.src_path)
            print ('Received modified event - %s.' % event.src_path)
        elif event.event_type == 'deleted':
            delete_file(event.src_path)
            print ('Received deleted event - %s.' % event.src_path)
        else:
            rebase()
            print('Rebase!')
            

w = Watcher(args.source, args.recursive)
w.run()