import tkinter as tk
from sys import stderr
import os
from random import shuffle, randrange
import PIL.ImageTk, PIL.ImageFile, PIL.Image

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True

IMAGE_TIME = 1000


def main():
	img = None
	done = False
	window = tk.Tk()
	window.configure(background="black")
	window.bind("<Key>", lambda e: e.widget.quit())
	window.attributes("-fullscreen", True)
	
	maxwidth, maxheight = window.winfo_screenwidth(), window.winfo_screenheight()
	
	panel = tk.Label(window)
	panel.pack()
	
	l = []
	
	def show_image(panel, seq):
		nonlocal img, done

		try:
			path = next(seq)
		except StopIteration:
			if done:
				print("finished")
				window.destroy()
			else:
				done = True
				print("Doing shuffled list")
				show_image(panel, (f for f in l))
			return
		print(path)
		try:
			im = PIL.Image.open(path)
			w, h = im.size
			ratio = min(maxwidth/w, maxheight/h)
			im = im.resize((int(ratio*w), int(ratio*h)), PIL.Image.ANTIALIAS)
			img = PIL.ImageTk.PhotoImage(image=im)
			panel.configure(image=img)
		except (tk.TclError, OSError, IOError) as e: #  May not be real image
			print(e, file=stderr)
			panel.after(0, show_image, panel, seq)
			return
		panel.after(IMAGE_TIME, show_image, panel, seq)
	
	def get_paths(dirs, l):
		for directory in dirs:
			for path, dirs, files in os.walk(directory):
				for f in files:
					if f.endswith(".png") or f.endswith(".jpg"):
						if not randrange(0, 1000):
							yield path + "/" + f
						else:
							l.append(path + "/" + f)
	
		shuffle(l)
		print("Finished making and shuffling list, length:", len(l))

	
	#pp = "/media/abel/abel_hd/Pictures/abstract/800 Impressive Abstract Full HD Wallpapers 1920 X 1080"
	#pp = "/media/abel/abel_hd/Pictures"
	pp = "/home/abel/Pictures"
	seq = get_paths((pp,), l)
	show_image(panel, seq)
	
	window.mainloop()

	

if __name__ == "__main__":
	main()
	

