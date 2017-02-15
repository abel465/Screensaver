from tkinter import Tk, Label
from argparse import ArgumentParser, ArgumentTypeError
from sys import stderr
from os import scandir
from random import shuffle, randrange
import PIL.ImageTk, PIL.ImageFile, PIL.Image
from itertools import chain


PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

BUFFER_SIZE = 1000
DISPLAY_CHANCE_INVERSE = 100
PRECACHE_DIR = 100
TOO_MANY_OPEN_FILES = 24
TOO_MANY_SYMLINK_LEVELS = 40


def positive_int(string):
    message = "'{}' is not a positive non zero integer".format(string)
    if not string.isdigit():
        raise ArgumentTypeError(message)
    x = int(string)
    if x <= 0:
        raise ArgumentTypeError(message)
    return x


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
            elif f.is_dir():
                iterators.append([f.path, None])
    shuffle(file_buffer)
    yield from file_buffer


def show_images(window, panel, seq, image_time, maxwidth, maxheight):
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
        except (OSError, IOError, FileNotFoundError) as e:  # May not be real image, IO problem. or file no longer there
            print(type(e).__name__, e, file=stderr)
            panel.after(0, show_images, window, panel, seq, image_time, maxwidth, maxheight)
        else:
            panel.after(image_time, show_images, window, panel, seq, image_time, maxwidth, maxheight)


def main(paths, image_time):
    window = Tk()
    window.configure(background="black")
    window.bind("<Key>", lambda e: e.widget.quit())
    window.attributes("-fullscreen", True)

    maxwidth, maxheight = window.winfo_screenwidth(), window.winfo_screenheight()

    panel = Label(window)
    panel.pack()

    seq = random_directory_walk(paths)
    show_images(window, panel, seq, image_time, maxwidth, maxheight)
    window.mainloop()


if __name__ == "__main__":
    parser = ArgumentParser(description="Screensaver program that works well with large quantity of media")
    parser.add_argument("-t", "--image_time", type=positive_int, help="The time in milliseconds that each image will stay on screen for")
    parser.add_argument("paths", nargs="+", help="A path for the screensaver to show media of")
    args = parser.parse_args()

    main(args.paths, args.image_time)
