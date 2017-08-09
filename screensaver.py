#!/usr/bin/env python3

from tkinter import Tk, Label
from argparse import ArgumentParser, ArgumentTypeError
from sys import stderr
from os import scandir
from random import shuffle, randrange
import PIL.ImageTk, PIL.ImageFile, PIL.Image
from itertools import chain
import cv2
import magic

#  keys
LEFT = 81
RIGHT = 83
DEFAULT = 255

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

BUFFER_SIZE = 1000
DISPLAY_CHANCE_INVERSE = 100
PRECACHE_DIR = 100
TOO_MANY_OPEN_FILES = 24
TOO_MANY_SYMLINK_LEVELS = 40
CALLBACK_BUFFER_SIZE = 10
HISTORY_LENGTH = 50

DEFAULT_TIME = 1000


class Callback(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        return self.func(*self.args, **self.kwargs)


def positive_int(string):
    message = "'{}' is not a positive non zero integer".format(string)
    if not string.isdigit():
        raise ArgumentTypeError(message)
    x = int(string)
    if x <= 0:
        raise ArgumentTypeError(message)
    return x


class Screensaver(Tk):
    def __init__(self, paths, image_time):
        super().__init__()
        self.callbacks = []
        self.history = []
        self.index = 0
        self.image_time = image_time
        self.configure(background="black")
        self.maxwidth, self.maxheight = self.winfo_screenwidth(), self.winfo_screenheight()
        self.seq = self.random_directory_walk(paths)

        self.bind("<Key>", lambda e: e.widget.quit())
        self.bind("<Left>", lambda e: self.previous_image() or self.show_images())
        self.bind("<Right>", lambda e: self.after_cancel(self.callback) or self.show_images())
        self.attributes("-fullscreen", True)
        self.panel = Label(self, border=0)
        self.panel.pack(expand=True)

        self.add_callbacks(1)
        self.show_images()

    def previous_image(self):
        self.index = max(0, self.index-2)
        self.after_cancel(self.callback)

    def play_video(self, path):
        try:
            cap = cv2.VideoCapture(path)
        except FileNotFoundError:
            return self.after(0, self.show_images)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cv2.namedWindow("frame", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("frame", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        ret = True
        ret, frame = cap.read()
        while(ret and cap.isOpened()):
            cv2.imshow("frame", frame)
            ret, frame = cap.read()
            key = cv2.waitKey(fps)
            if key == RIGHT:
                break
            elif key == LEFT:
                self.previous_image()
                break
            elif key != DEFAULT:
                cap.release()
                cv2.destroyAllWindows()
                exit()
        cap.release()
        cv2.destroyAllWindows()
        self.attributes("-fullscreen", True)
        return self.after(0, self.show_images)

    def random_directory_walk(self, dirs):
        file_buffer = []
        shuffle(dirs)
        iterators = [[d, None] for d in dirs]

        while iterators:
            n = randrange(0, len(iterators))
            directory, iterator = iterators[n]
            if not iterator:
                try:
                    while True:
                        try:
                            iterator = scandir(directory)
                        except OSError as e:
                            if e.errno == TOO_MANY_OPEN_FILES:
                                for i in range(len(iterators)):
                                    if iterators[i][1]:
                                        #  evaluating next PRECACHE_DIR images to close files
                                        evaluation = tuple(next(iterators[i][1]) for _ in range(PRECACHE_DIR))
                                        iterators[i][1] = chain(evaluation, iterators[i][1])
                            else:
                                raise e
                        else:
                            break
                    iterators[n][1] = iterator
                except PermissionError as e:
                    print("PermissionError", e, file=stderr)
                    del iterators[n]
                    continue
                except FileNotFoundError as e:
                    print("FileNotFoundError", e, file=stderr)
                    continue
            try:
                f = next(iterator)
            except StopIteration:
                del iterators[n]
                continue
            if f.is_file(follow_symlinks=False):
                if not randrange(0, DISPLAY_CHANCE_INVERSE):
                    yield f.path
                elif len(file_buffer) == BUFFER_SIZE:
                    yield file_buffer.pop(randrange(0, len(file_buffer)))
                else:
                    file_buffer.append(f.path)
            elif f.is_dir(follow_symlinks=False):
                iterators.append([f.path, None])
        shuffle(file_buffer)
        yield from file_buffer

    def display_image(self, image):
        self.panel.configure(image=image)
        return self.after(self.image_time, self.show_images)

    def display_animated_gif(self, frames, delay, i=0):
        if i < len(frames)-1:
            self.callback = self.after(delay, self.display_animated_gif, frames, delay, i+1)
        else:
            self.callback = self.after(0, self.show_images)
        self.panel.configure(image=frames[i])
        return self.callback

    def get_callback(self, path):
        try:
            file_info = magic.from_file(path, True).lower()
        except (PermissionError, magic.MagicException) as e:
            print(type(e).__name__, e, file=stderr)
            return
        if "video" in file_info:
            print(path)
            return Callback(self.play_video, path)
        elif "image" in file_info:
            try:
                if "gif" in file_info:
                    i = 0
                    frames = []
                    im = PIL.Image.open(path)
                    delay = im.info["duration"]
                    w, h = im.size
                    ratio = min(self.maxwidth/w, self.maxheight/h)
                    im_resized = im.resize((int(ratio*w), int(ratio*h)), PIL.Image.ANTIALIAS)
                    try:
                        while True:
                            frames.append(PIL.ImageTk.PhotoImage(image=im_resized))
                            i += 1
                            im.seek(i)
                            im_resized = im.resize((int(ratio*w), int(ratio*h)), PIL.Image.ANTIALIAS)
                    except EOFError:
                        print(path)
                        if len(frames) == 1:
                            return Callback(self.display_image, frames[0])
                        else:
                            return Callback(self.display_animated_gif, frames, delay)
                else:
                    im = PIL.Image.open(path)
                    w, h = im.size
                    ratio = min(self.maxwidth/w, self.maxheight/h)
                    im = im.resize((int(ratio*w), int(ratio*h)), PIL.Image.ANTIALIAS)
                    img = PIL.ImageTk.PhotoImage(image=im)
                    print(path)
                    return Callback(self.display_image, img)
            except (OSError, FileNotFoundError, IOError) as e:  # May not be real image, File no longer there, IO problem
                print(type(e).__name__, e, file=stderr)

    def add_callbacks(self, n):
        count = 0
        while count < n:
            try:
                path = next(self.seq)
            except StopIteration:
                break
            callback = self.get_callback(path)
            if callback:
                self.callbacks.append(callback)
                count += 1

    def show_images(self):
        try:
            if self.index < len(self.history):
                callback = self.history[self.index]
            else:
                callback = self.callbacks.pop(0)
                self.history.append(callback)
                if len(self.history) > HISTORY_LENGTH:
                    del self.history[0]
            self.index += 1
        except IndexError:  # Finished
            self.destroy()
            return

        self.callback = callback.run()
        if len(self.callbacks) < CALLBACK_BUFFER_SIZE:
            self.add_callbacks(2)


def main(paths, image_time):
    screensaver = Screensaver(paths, image_time)
    screensaver.mainloop()


if __name__ == "__main__":
    parser = ArgumentParser(description="Screensaver program that works well with large quantity of media")
    parser.add_argument("-t", "--image_time", type=positive_int, help="The time in milliseconds that each image will stay on screen for")
    parser.add_argument("paths", nargs="+", help="A path for the screensaver to show media of")
    args = parser.parse_args()

    main(args.paths, args.image_time or DEFAULT_TIME)
