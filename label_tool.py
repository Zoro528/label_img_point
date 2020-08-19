from __future__ import division
from tkinter import *
from tkinter.filedialog import askdirectory
from PIL import Image, ImageTk
import os
import glob


class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.pointfilename = ''
        self.tkimg = None
        self.origin_img = 0

        # initialize point dict
        self.POINTS = {}
        self.nums = 0

        # ----------------- GUI stuff ---------------------
        # shortcut keys
        self.parent.bind("<BackSpace>", self.cancel_point)
        self.parent.bind("a", self.pre_image)  # press 'a' to go backforward
        self.parent.bind("d", self.next_image)  # press 'd' to go forward

        # dir entry & load
        self.labImageDir = Label(self.frame, text="Image Directory:")
        self.labImageDir.grid(row=0, column=0, sticky=E)
        global path
        path = StringVar()
        self.entImageDir = Entry(self.frame, textvariable=path)
        self.entImageDir.grid(row=0, column=1, sticky=W + E)
        # Browse Button
        self.btnBrowse = Button(
            self.frame, text="Browse", command=self.select_path)
        self.btnBrowse.grid(row=0, column=2, sticky=W + E)

        # panel for show entire image
        self.cavImage = Canvas(self.frame, cursor='tcross')
        self.cavImage.bind("<Button-1>", self.mouse_click)
        self.cavImage.bind("<Motion>", self.mouse_move)
        self.cavImage.grid(row=2, column=1, rowspan=6, sticky=W + N)

        # magnifier
        self.cavMagnifier = Canvas(
            self.frame, width=500, height=500, bg='white')
        self.cavMagnifier.grid(row=2, column=0, rowspan=6, sticky=N + E)
        self.cavMagnifier.create_text(250, 250, text='+',
                                      font='Arial -40', fill='red')

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Points:' + str(self.nums))
        self.lb1.grid(row=1, column=2,  sticky=W+N)
        self.pointlistbox = Listbox(self.frame, width=22, height=22)
        self.pointlistbox.grid(row=2, column=2, sticky=N)
        self.btnDel = Button(self.frame, text='Delete',
                             command=self.delete_point)
        self.btnDel.grid(row=3, column=2, sticky=W+E+N)
        # clear button
        self.btnClear = Button(
            self.frame, text='ClearAll', command=self.clear_all)
        self.btnClear.grid(row=4, column=2, sticky=W + E + N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=10, column=1, columnspan=2, sticky=W+E)

        self.prevBtn = Button(self.ctrPanel, text='<< Prev',
                              width=10, command=self.pre_image)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>',
                              width=10, command=self.next_image)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.goto_image)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        # self.frame.columnconfigure(1, weight=1)
        # self.frame.rowconfigure(4, weight=1)

        self.ratio = 1.

    def load_dir(self):
        self.category = self.entImageDir.get()
        self.parent.focus()

        # get image list
        self.imageDir = self.category
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.jpg')))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.jpeg')))
        self.imageList.extend(glob.glob(os.path.join(self.imageDir, '*.bmp')))
        if len(self.imageList) == 0:
            print('No . images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = self.imageDir + '/Labels'
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.load_image()

    def select_path(self):
        path_ = askdirectory()
        if path != '':
            path.set(path_)
        if path.get() != '':
            self.load_dir()

    # load self.cur-1 image
    def load_image(self):
        imagepath = self.imageList[self.cur - 1]
        pil_img = Image.open(imagepath)
        self.origin_img = pil_img
        # resize to 800*449
        global w0, h0
        w0, h0 = pil_img.size
        ratio1 = 800 / w0
        ratio2 = 500 / h0
        if ratio1 > 1 and ratio2 > 1:
            self.ratio = 1
        else:
            self.ratio = min(ratio1, ratio2)
        w = int(w0 * self.ratio)
        h = int(h0 * self.ratio)

        self.resize_img = pil_img.resize((w, h), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(self.resize_img)
        self.cavImage.config(width=max(self.tkimg.width(), w),
                             height=max(self.tkimg.height(), h))
        self.cavImage.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.POINTS.clear()
        labelname = os.path.split(imagepath)[-1].split('.')[0] + '.txt'
        self.pointfilename = os.path.join(self.outDir, labelname)

        if os.path.exists(self.pointfilename):
            with open(self.pointfilename) as f2:
                if not f2:
                    return
                for line in f2.readlines():
                    self.nums += 1
                    point = tuple(int(num) for num in line.split())
                    self.pointlistbox.insert(END, str(point))
                    start = point[0] * self.ratio
                    end = point[1] * self.ratio
                    point_id = self.cavImage.create_line(
                        start - 1, end - 1, start + 1, end + 1, width=4, fill='red')
                    self.POINTS[point_id] = point

                self.lb1.config(text="Points:" + str(self.nums))

    def save_image(self):
        with open(self.pointfilename, 'w') as f2:
            for key, point in self.POINTS.items():
                f2.write(' '.join(map(str, point)))
                f2.write('\n')

    def mouse_move(self, event):
        real_x = int(event.x // self.ratio)
        real_y = int(event.y // self.ratio)

        # display position
        self.disp.config(text='x: %d, y: %d' % (real_x, real_y))

        # Magnifier
        if self.origin_img:
            region = self.origin_img.crop(
                (real_x - 250, real_y-250, real_x+250, real_y+250))
            region = region.resize((500, 500), Image.ANTIALIAS)
            self.tk_resize_img = ImageTk.PhotoImage(region)
            self.cavMagnifier.create_image(
                0, 0, image=self.tk_resize_img, anchor=NW)
            self.cavMagnifier.create_text(250, 250, text='+',
                                          font='Arial -40', fill='red')

    def mouse_click(self, event):
        point = (int(event.x // self.ratio), int(event.y // self.ratio))
        point_id = self.cavImage.create_line(
            event.x - 1, event.y - 1, event.x + 1, event.y + 1, width=4, fill='red')
        self.POINTS[point_id] = point
        self.nums += 1
        self.pointlistbox.insert(END, str(point))
        self.lb1.config(text="Points:" + str(self.nums))

    def cancel_point(self, evet):
        if len(self.POINTS) == 0:
            return
        self.delete_point(last=True)

    def delete_point(self, last=False):
        idx = self.pointlistbox.curselection()
        if self.pointlistbox.size() == 0:
            return
        idx = self.pointlistbox.size() - 1 if not idx else idx[0]
        self.nums -= 1
        point = self.pointlistbox.get(idx)
        self.pointlistbox.delete(idx)
        if last == True:
            item = self.POINTS.popitem()
            self.cavImage.delete(item[0])
        else:
            for key, value in self.POINTS.items():
                if point == str(value):
                    self.POINTS.pop(key)
                    self.cavImage.delete(key)
                    break
        self.lb1.config(text="Points:" + str(self.nums))

    def clear_all(self):
        for idx in self.POINTS.keys():
            self.cavImage.delete(idx)
        self.POINTS.clear()
        self.pointlistbox.delete(0, self.nums)
        self.nums = 0
        self.lb1.config(text="Points:" + str(self.nums))

    def pre_image(self, event=None):
        if self.cur > 1:
            self.cur -= 1
            self.pic_init()

    def next_image(self, event=None):
        if self.cur < self.total:
            self.cur += 1
            self.pic_init()

    def goto_image(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.cur = idx
            self.pic_init()

    def pic_init(self):
        self.save_image()
        self.POINTS.clear()
        self.pointlistbox.delete(0, END)
        self.nums = 0
        self.load_image()


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=True, height=True)
    root.mainloop()
