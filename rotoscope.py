from __future__ import print_function
import os
from os.path import dirname, abspath

import uuid
import shlex
import subprocess
import sys
import threading
from PIL import Image

import time

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

files_q = Queue()


def extract_frames(film=None, work_dir=None):
    command = (
        "ffmpeg -i {film} "
        "-f image2 -pix_fmt bgr24 %03d.bmp").format(
            film=film,
            outdir=work_dir)
    print(command)
    subprocess.call(command, shell=True)


def trace_file(work_file=None, tracer=None):
    fn, ext = os.path.splitext(work_file)

    autotrace_cmd = (
        "autotrace {input} "
        "-output-format svg "
        "-color-count 16 "
        "-despeckle-level 19 "
        "-despeckle-tightness 0.45 "
        "-filter-iterations 25 "
        "-output-file {output}.svg").format(
            input=work_file,
            output=fn)

    # Setup the tracers
    if tracer == 'autotrace':
        trace_command = autotrace_cmd

    elif tracer == 'potrace':
        trace_command = "potrace -t 25 -s -k .5 -a 2 {0}".format(work_file)

#    if tracer == 'both':
#        a_svg =
#        im1 =

    # Call the tracer
    subprocess.call(shlex.split(trace_command))

    # Convert traced file back to img format for ffmpeg
    convert_back = "convert {fn}.svg {fn}.bmp".format(fn=fn)
    subprocess.call(shlex.split(convert_back))

    # Remove working files
    # subprocess.call(shlex.split('rm {0}'.format(work_file)))
    # subprocess.call(shlex.split('rm {0}.svg'.format(fn)))


def trace_thread(q, tracer):
    while True:
        work_file = q.get()
        print("FRAMES REMAINING: ", q.qsize())
        trace_file(work_file=work_file, tracer=tracer)
        q.task_done()


def autotrace(tracer=None):
    files = os.listdir('.')
    [files_q.put(f) for f in files]
    print("QUEUE SIZE IS ", files_q.qsize())

    for x in range(8):
        t = threading.Thread(target=trace_thread, args=(files_q, tracer))
        t.daemon = True
        t.start()


def create_new_video(tmp_dir):
    cmd = "../imgs_to_mp4.sh {tmp_dir} ../{out_file}".format(
        tmp_dir=tmp_dir,
        out_file='out{0}.mp4'.format(time.time()))
    subprocess.call(cmd, shell=True)
    subprocess.call('rm *.bmp', shell=True)

if __name__ == '__main__':
    a = time.time()
    BASE_DIR = dirname(abspath(__file__))
    wrkdir = "work_{0}".format(uuid.uuid4().hex)
    film_name = os.path.abspath(sys.argv[1])
    tracer = sys.argv[2]
    print('making directory: ', wrkdir)
    os.mkdir(wrkdir)
    os.chdir(wrkdir)

    extract_frames(film=film_name, work_dir=wrkdir)
    autotrace(tracer=tracer)
    files_q.join()
    create_new_video(tmp_dir=wrkdir)

    print("total time taken", time.time() - a)
