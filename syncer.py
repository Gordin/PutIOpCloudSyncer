
import sys
import time
from multiprocessing import Process, Manager
from collections import namedtuple
import putiopy
from pcloud import PyCloud
from sh import mv, rm, aria2c

TMPDIR = '/home/gordin/tmp'
#helper = putiopy.AuthHelper(CLIENTID, SECRET 'xxx.xxx', type='token')

PCLOUD_USER = XXX
PCLOUD_PASS = XXX
PUTIO_KEY = XXX

FileEntry = namedtuple('FileEntry', ['name', 'download_link'])

def filename(file):
    return '{}/{}'.format(TMPDIR, file.name)

def process_output(line):
    print(line)

class PutIOpCloudSyncer(object):
    def __init__(self):
        manager = Manager()
        self.pcloud = PyCloud(PCLOUD_USER, PCLOUD_PASS)
        self.putio = putiopy.Client(PUTIO_KEY)
        self.download_list = manager.list()
        self.upload_list = manager.list()
        self.files_left = manager.Value(1, 0)
        self.destination = None

    def download(self, file):
        print('Download of {} started'.format(file.name))
        aria2c('-d', TMPDIR, '-o', file.name, '--continue=true', '-x3', file.download_link)
        print('Download finished')


    def upload(self, file):
        print('Starting upload of {}'.format(file.name))
        self.pcloud.uploadfile(path=self.destination, files=['{}/{}'.format(TMPDIR, file.name)])
        print('Finished upload')


    def cleanup(self, file):
        print('Removing local copy of {}'.format(file.name))
        rm(filename(file))
        print('Removed successfully')


    def process_folder(self, folder):
        files = folder.dir() if folder.file_type == 'FOLDER' else [folder]
        for file in files:
            self.enqueue_file(file)
        print("Files to sync: {}".format(self.files_left.get()))
        uploader = Process(target=self.file_uploader)
        downloader = Process(target=self.file_downloader)
        uploader.start()
        downloader.start()
        uploader.join()
        downloader.join()
        # fs = {
        #     executor.submit(self.file_uploader): "uploader",
        #     executor.submit(self.file_downloader): "downloader"
        # }
        # for future in concurrent.futures.as_completed(fs):
        #     tag = fs[future]
        #     print("Result of {}: ".format(tag, future.result()))


    def enqueue_file(self, file):
        self.download_list.append(FileEntry(file.name, file.get_download_link()))
        self.files_left.set(self.files_left.get() + 1)


    def list_paths(self):
        file_list = self.putio.File.list()
        folders = [x for x in file_list if x.name in ('Serien', 'Filme')]
        for path in [folder for fs in folders for folder in fs.dir()]:
            print(path.name, path.id)


    def filter_paths(self, name):
        file_list = self.putio.File.list()
        folders = [x for x in file_list if x.name in ('Serien', 'Filme')]
        files = [file for folder in folders for file in folder.dir()]
        file = list(filter(lambda x: x.name.startswith(name), files))
        if file:
            if len(file) > 1:
                print("More than 1 possible folder", file)
                sys.exit(1)
            return file[0]
        print('No Matching file')
        sys.exit(1)


    def file_downloader(self):
        print("File Downloader started")
        while self.download_list:
            file = self.download_list.pop()
            self.download(file)
            self.upload_list.append(file)
        print("File Downloader stopped")


    def file_uploader(self):
        print("File Uploader started")
        while self.files_left.get():
            print('Files left to upload: {}'.format(self.files_left.get()))
            print('Files to upload in queue: {}'.format(len(self.upload_list)))
            while not self.upload_list:
                print('Waiting for something to upload...')
                time.sleep(10)
            while self.upload_list:
                file = self.upload_list.pop()
                self.upload(file)
                self.cleanup(file)
                self.files_left.set(self.files_left.get() - 1)
        print("File Uploader stopped")


    def sync(self):
        if sys.argv[1] == 'list':
            self.list_paths()
        elif sys.argv[1] == 'filter':
            path = self.filter_paths(sys.argv[2])
            print('Selected Path: {}'.format(path.name))
        elif sys.argv[1] == 'sync':
            path = self.filter_paths(sys.argv[2])
            print('Selected Path: {}'.format(path.name))
            self.destination = sys.argv[3]
            self.process_folder(path)
            print("Started downloader and uploader")

if __name__ == '__main__':
    syncer = PutIOpCloudSyncer()
    syncer.sync()
