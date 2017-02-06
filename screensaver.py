from collections import OrderedDict
import tkinter as tk
# from sortedcontainers import SortedListWithKey
import argparse
from sys import stderr
import os
from random import shuffle, randrange, randint
import PIL.ImageTk, PIL.ImageFile, PIL.Image
# import bisect

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_TIME = 100
BUFFER_LENGTH = 30


#def next_ten(seq):
#	for i in range(10):
#		yield next(seq)

def random_directory_walk(dirs):
	shuffle(dirs)
	#iterators = [iter(d) for d in dirs]
	while dirs:
		directory = dirs.pop()
		for f in os.scandir(directory):
			if f.is_file():
				if is_image(f.name):
					yield directory + "/" + f.name
			elif f.is_dir():
				dirs.insert(randint(0, len(dirs)), directory + "/" + f.name)

"""def random_os_walk(dirs):
	if not dirs:
		return
	#print(dirs)
	shuffle(dirs)
	new_dirs = []
	for directory in dirs:
		for f in os.scandir(directory):
#			print("f:", f.name, f.is_file, f.is_dir())
			if f.is_file():
				if is_image(f.name):
					yield f.name
			elif f.is_dir():  # is directory?
				#print("dir:", f.name)
				new_dirs.append(directory + "/" + f.name)
	#print(new_dirs)
	yield from random_os_walk(new_dirs)"""
			
			

def bisect_right(a, x):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(x) will
    insert just after the rightmost x already there.

    MODIFIED FROM bisect.bisect_right SOURCECODE
    """

    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo+hi) // 2
        if x < a[mid][0]:
            hi = mid
        else:
            lo = mid + 1
    return lo

# def get_files(directory, indices, nums):
#     n = 0
#     # indices = [t[0] for t in v]
#     for f in os.scandir(directory):
#         if f.isfile and f.endswith(".png") or f.endswith(".jpg") or f.endswith(".svg"):
#             if n in indices:
#                 yield f.name, nums[indices.index(n)], directory
#                 indices.remove(n)
#                 if not indices:
#                     return
#             n += 1

counter = {}

def main(paths):
    img = None
    window = tk.Tk()
    window.configure(background="black")
    window.bind("<Key>", lambda e: e.widget.quit())
    window.attributes("-fullscreen", True)

    maxwidth, maxheight = window.winfo_screenwidth(), window.winfo_screenheight()

    panel = tk.Label(window)
    panel.pack()

    directory_locations = []

    def show_images(panel, seq):
        nonlocal img

        try:
            path = next(seq)
        except StopIteration:
            window.destroy()
            return
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
            panel.after(0, show_images, panel, seq)
            return
        panel.after(IMAGE_TIME, show_images, panel, seq)

    """
    def get_paths(dirs):
        used = []
        total = 0
        for f in random_directory_walk(dirs):
            #if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".svg"):
            total += 1
            if not randrange(0, 1000):
                yield s
        if total:
            directory_locations.append([total, path])

        directory_locations.sort(key=lambda pair: pair[0])
        # print(directory_locations)
        # print()
        for i in range(1, len(directory_locations)):
            directory_locations[i][0] += directory_locations[i-1][0]

        # print()
        # print(directory_locations)
        # print(directory_locations[-1][0])
        print("Finished counting number of media files:", directory_locations[-1][0])
        nums = list(range(directory_locations[-1][0]))
        shuffle(nums)
        # print(nums)
        # for x in [0, 1, 2 , 3, 4, 777, 762, 763, 764, 765, 5735]:
        i = 0
        j = BUFFER_LENGTH
        length = len(nums)
        while length > i:
            # print(i, j)
            d = OrderedDict()  # maps directories to indices of the directories
            dd = OrderedDict()  # maps directories to indices of the whole structure
            ez = nums[i:j]
            # print("ez:", ez, len(nums))
            # map_back = {}  # maps indices of the whole structure to directory and indices of the directories pairs
            for x in ez:'
                # x = 1#directory_locations[-1][0]-1
                # print("x:", x)
                a = bisect_right(directory_locations, x)
                # print(a)
                # try:
                # print(directory_locations[a], end=" ")
                if a == 0:
                    index = x
                    # print(x)
                else:
                    index = x-directory_locations[a-1][0]
                    # print(x-directory_locations[a-1][0])
                directory = directory_locations[a][1]
                if directory in d:
                    d[directory].append(index)
                    dd[directory].append(x)
                else:
                    d[directory] = [index]
                    dd[directory] = [x]
                # map_back[x] = (directory, index)


            ll = []
            dd_gen = iter(dd.items())
            for k, v in d.items():  # directory, index
                _, numss = next(dd_gen)
                ll.extend(get_files(k, v, numss))
            # print("ll:", ll)#[x[1] for x in ll])
            ll.sort(key=lambda x:ez.index(x[1]))
            yield from (x[2] + "/" + x[0] for x in ll)
            # print("ll:", [x[1] for x in ll])

            i = j
            j += BUFFER_LENGTH
        print(counter)
    """

    seq = random_directory_walk(paths)
    show_images(panel, seq)
    window.mainloop()

def is_image(s):
    return s.endswith(".png") or s.endswith(".jpg") or s.endswith(".svg")

def get_files(directory, indices, nums):
    # print(indices, nums)
    if directory in counter:
        counter[directory] += 1
    else:
        counter[directory] = 1
    n = 0
    # indices = [t[0] for t in v]
    for f in os.scandir(directory):
        # help(f)
        if f.is_file and is_image(f.name):
            if n in indices:
                # print(n, indices.index(n), indices)
                yield f.name, nums[indices.index(n)], directory
                # indices.remove(n)
                if not indices:
                    return
            n += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screensaver program that works well with large quantity of media")
    parser.add_argument("image_time", help="The time that an image will stay on screen for")
    parser.add_argument("paths", nargs="+", help="A path for the screensaver to show media of")
    args = parser.parse_args()
    # print(args.paths)
    #exit
    #print(args.paths)
    #for x in random_os_walk(args.paths[:]):
    #	print(x)
    #print(args.paths)
    #print(list(list(os.walk(p)) for p in args.paths))
    main(args.paths)
