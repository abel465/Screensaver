import tkinter as tk
import argparse
from sys import stderr
import os
from os import scandir
from random import shuffle, randrange
import PIL.ImageTk, PIL.ImageFile, PIL.Image
from itertools import chain


PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_TIME = 400
BUFFER_SIZE = 1000
DISPLAY_CHANCE_INVERSE = 100
PRECACHE_DIR = 100
TOO_MANY_OPEN_FILES = 24
TOO_MANY_SYMLINK_LEVELS = 40


def is_image(s):
    return s.endswith(".png") or s.endswith(".jpg") or s.endswith(".svg")


def random_directory_walk(dirs):
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
                        ez = scandir(directory)
                    except OSError as e:
                        raise e
                        if e.errno == TOO_MANY_OPEN_FILES:
                            for i in range(len(iterators)):
                                if iterators[i][1]:
                                    # evaluating next PRECACHE_DIR images to close files
                                    evalutaion = tuple(next(iterators[i][1]) for _ in range(PRECACHE_DIR))
                                    iterators[i][1] = chain(evaluation, iterators[i][1])
                        else:
                            raise e
                    else:
                        break
                iterator = ez
                iterators[n][1] = iterator
            except PermissionError as e:
                print("PermissionError", e, file=stderr)
                del iterators[n]
                continue
        try:
            f = next(iterator)
        except StopIteration:
            del iterators[n]
            continue
        try:
            is_file = f.is_file()
        except OSError as e:
            if e.errno != TOO_MANY_SYMLINK_LEVELS:
                raise e
        else:
            if is_file:
                if is_image(f.name):
                    if not randrange(0, DISPLAY_CHANCE_INVERSE):
                        yield f.path
                    elif len(file_buffer) == BUFFER_SIZE:
                        yield file_buffer.pop(randrange(0, len(file_buffer)))
                    else:
                        file_buffer.append(f.path)
            elif f.is_dir() or f.is_symlink():
                iterators.append([f.path, None])
    shuffle(file_buffer)
    yield from file_buffer


def show_images(window, panel, seq, maxwidth, maxheight):
    global img  # prevents image being garbage collected

    try:
        path = next(seq)
    except StopIteration:
        window.destroy()
    else:
        print(path)
        try:
            im = PIL.Image.open(path)
            w, h = im.size
            ratio = min(maxwidth/w, maxheight/h)
            im = im.resize((int(ratio*w), int(ratio*h)), PIL.Image.ANTIALIAS)
            img = PIL.ImageTk.PhotoImage(image=im)
            panel.configure(image=img)
        except (OSError, IOError) as e:  # May not be real image, or IO problem
            print(e, file=stderr)
            panel.after(0, show_images, window, panel, seq, maxwidth, maxheight)
        else:
            panel.after(IMAGE_TIME, show_images, window, panel, seq, maxwidth, maxheight)


def main(paths):
    window = tk.Tk()
    window.configure(background="black")
    window.bind("<Key>", lambda e: e.widget.quit())
    window.attributes("-fullscreen", True)

    maxwidth, maxheight = window.winfo_screenwidth(), window.winfo_screenheight()

    panel = tk.Label(window)
    panel.pack()

    seq = random_directory_walk(paths)
    show_images(window, panel, seq, maxwidth, maxheight)
    window.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screensaver program that works well with large quantity of media")
    parser.add_argument("image_time", help="The time that an image will stay on screen for")
    parser.add_argument("paths", nargs="+", help="A path for the screensaver to show media of")
    args = parser.parse_args()
    # summ = 0
    # for path, dirs, files in os.walk(args.paths[0]):
    #     summ += sum(1 for f in files if is_image(f))
    # print(summ)
    # print(sum(1 for f in random_directory_walk(args.paths)))
    main(args.paths)
