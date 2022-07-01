from pickle import FRAME
from .globals import *

from .image_get import *
from .image_filter import *

from math import floor, ceil

LG = (0.5, 0.5, 0.5, 1)
DG = (0.25, 0.25, 0.25, 1)
CHECKER_SIZE = 8
CHECKERBOARD = numpy.repeat(
    numpy.repeat(
        numpy.array(((LG, DG), (DG, LG)), dtype=numpy.float32),
        CHECKER_SIZE, axis=1
    ), CHECKER_SIZE, axis=0
)
ALL = [0, 0]

def make_checkerboard(w, h):
    sw = ceil(w / CHECKER_SIZE / 2)
    sh = ceil(h / CHECKER_SIZE / 2)
    return numpy.tile(CHECKERBOARD, (sh,sw,1))[:h,:w]


class ImageStacker:
    ZOOM_LEVELS = [0.2, 0.25, 1/3, 0.5, 2/3, 0.75, 1, 2, 3, 4, 5, 6, 7, 8]
    ZOOM_WIDTH = 300
    ZOOM_PART = ZOOM_WIDTH / len(ZOOM_LEVELS)

    def __init__(self):
        self.size = None
        self.zoom = 2
        self.frame = 0
        self.subframe = 0
        self.subframecap = 0
        self.pan = (0, 0)
        self.scroll = (0, 0)
        self.panning = False
        self.image = None

        with gui.handler_registry():
            gui.add_mouse_drag_handler(callback=lambda s,a: self.update_pan(a))
            gui.add_mouse_release_handler(callback=lambda: self.end_pan())
            gui.add_mouse_wheel_handler(callback=lambda: self.adjust_pan())
        with gui.item_handler_registry() as self.ph:
            gui.add_item_clicked_handler(callback=lambda: self.start_pan(), button=0)

        with gui.child_window(width=-1, height=-2):
            with gui.group(tag="zoombar", horizontal=True):
                self.zoomer = gui.add_slider_int(
                    min_value=0,
                    max_value=len(ImageStacker.ZOOM_LEVELS)-1,
                    default_value=ImageStacker.ZOOM_LEVELS.index(self.zoom),
                    callback=lambda: self.update_zoom(),
                    width=ImageStacker.ZOOM_WIDTH,
                    format=''
                )
                self.zoom_label = gui.add_text("")

                gui.add_spacer(width=40)

                with gui.group(tag="animatebar", horizontal=True, show=False):
                    gui.add_text("Animation:")
                    self.animation = gui.add_combo([], width=-1, callback=lambda: self.change_animation())
            
            with gui.child_window(width=-1, pos=(0, 40), border=False) as self.cwin:
                self.bgtex = gui.add_raw_texture(1, 1, numpy.array([0,0,0,0], dtype=numpy.float32), parent="texreg")
                self.fgtex = gui.add_raw_texture(1, 1, numpy.array([0,0,0,0], dtype=numpy.float32), parent="texreg")
                self.bg = gui.add_image(self.bgtex, pos=(10, 0), show=False)
                self.fg = gui.add_image(self.fgtex, pos=(10, 0), show=False)
                gui.bind_item_handler_registry(self.fg, self.ph)

            self.update_zoom()
    
    def update_zoom(self):
        with SAFETY_LOCK:
            # Calculate new zoom
            zi = gui.get_value(self.zoomer)
            zoom = ImageStacker.ZOOM_LEVELS[zi]

            # Update label
            gui.set_value(self.zoom_label, f'{floor(zoom * 100 + 0.5)}%')

            # Move pan
            self.zoom = zoom

            # Update image based on zoom
            G.app.change()
    
    def start_pan(self):
        self.panning = True
        self.pan = (0, 0)
        self.adjust_pan()
    def end_pan(self):
        self.panning = False
    def adjust_pan(self):
        self.scroll = (gui.get_x_scroll(self.cwin), gui.get_y_scroll(self.cwin))
    def update_pan(self, appdata):
        if self.panning:
            px = appdata[1] - self.pan[0]
            py = appdata[2] - self.pan[1]
            self.pan = (appdata[1], appdata[2])

            if px != 0 or py != 0:
                sx, sy = self.scroll
                nx = max(0, min(sx - px, gui.get_x_scroll_max(self.cwin)))
                ny = max(0, min(sy - py, gui.get_y_scroll_max(self.cwin)))
                gui.set_x_scroll(self.cwin, nx)
                gui.set_y_scroll(self.cwin, ny)
                self.scroll = nx, ny
    
    def get_animation(self):
        try:
            animation = gui.get_value(self.animation).replace(" ", "_").lower()
            if not animation: return None
            return G.types[G.active_type]["animations"][animation][tuple(self.image.size)]
        except Exception:
            return None

    def change_animation(self):
        # To keep fluidity when switching animations, the frame and subframe are not reset.
        # In update(), frame is moduloed, so no issues there.
        # self.frame = 0
        # self.subframe = 0

        atype = self.get_animation()
        if atype:
            self.subframecap = atype["delay"]
        G.app.animation_change()
    
    def update_animation(self, delta):
        if self.subframe >= self.subframecap:
            with FRAME_LOCK:
                self.frame += 1
                self.subframe -= self.subframecap
            G.app.animation_change()
        self.subframe += delta

    def update_image(self):
        # Delete image if nothing is selected
        if not G.active_type:
            self.size = None
            self.image = None
            return

        # Now build the image
        typ = G.types[G.active_type]
        nsize = typ["size"]

        # Collect images
        imgs = []
        for item, pobj in typ["draw_order"].items():
            img = get_image(typ["parts"], item)
            if img:
                # Calculate priority (and bounding boxes)
                priority = get_pnum(pobj, item, nsize)

                # Append to image list
                if type(priority) == list:
                    if type(img) == tuple:
                        # Tuple means 
                        for i, v in enumerate(img):
                            if v:
                                for p, box in priority:
                                    imgs.append(((p, i), v, box))
                    else:
                        # Single image, but with multiple bounding boxes
                        for p, box in priority:
                            imgs.append(((p, -1), img, box))
                else:
                    if type(img) == tuple:
                        # Multiple images
                        for i, v in enumerate(img):
                            if v:
                                imgs.append(((priority, i), v, None))
                    else:
                        # Single image
                        imgs.append(((priority, -1), img, None))
        
        # Sort images
        # print(imgs)
        imgs.sort(key=lambda x: x[0])

        # Stack images
        outimg = Image.new("RGBA", nsize)
        for _, img, box in imgs:
            if type(img) == list:
                if box:
                    for i in img:
                        outimg.alpha_composite(i, (box[0], box[1]), tuple(box))
                else:
                    for i in img:
                        outimg.alpha_composite(i)
            else:
                if box:
                    outimg.alpha_composite(img, (box[0], box[1]), tuple(box))
                else:
                    outimg.alpha_composite(img)

        # Apply filters
        if "filters" in typ:
            checkboxes = G.active["checkboxes"]
            filters = [(filter.get("priority", 0), filter) for filter in typ["filters"]]
            filters.sort(key=lambda v: v[0])

            for _, filter in filters:
                # Recursive filter application
                outimg = apply_filter(outimg, filter, checkboxes)
        
        # Save outimg for modification later
        self.image = outimg

    def update(self):
        img = self.image

        if not img:
            # No image to show, so just hide the image viewer
            gui.configure_item(self.bg, show=False)
            gui.configure_item(self.fg, show=False)
            return
        
        # There is an image to show
        w, h = self.image.size

        # Cut the image based on animations
        atype = self.get_animation()
        if atype:
            frames = atype["frames"]
            grid = atype["grid"]

            with FRAME_LOCK:
                self.frame %= len(frames)
                frame = frames[self.frame]

            w = w / grid[0]
            h = h / grid[1]

            img = img.crop((
                int(frame % grid[0] * w),
                int(frame // grid[1] * h),
                int(frame % grid[0] * w + w),
                int(frame // grid[1] * h + h),
            ))

            w, h = img.size

        # Zoom the image
        with SAFETY_LOCK:
            zoom = self.zoom
            zsize = int(w*zoom), int(h*zoom)
        
        if zoom != 1:
            resample = Image.Resampling.BICUBIC
            if gui.get_value("nearest") and zoom > 1:
                resample = Image.Resampling.NEAREST

            img = img.resize(zsize, resample=resample)
        
        # Convert img to numpy array
        data = numpy.divide(numpy.array(img, dtype=numpy.float32), 255)

        # Resize if necessary
        if self.size == zsize:
            # Resize not necessary
            gui.set_value(self.fgtex, data)
        else:
            # Resize is necessary
            self.size = zsize
            zw, zh = zsize

            bgtex = gui.add_raw_texture(zw, zh, make_checkerboard(zw, zh).ravel(), parent="texreg")
            fgtex = gui.add_raw_texture(zw, zh, data, parent="texreg")
            
            gui.configure_item(self.bg, texture_tag=bgtex, width=zw, height=zh, show=True)
            gui.configure_item(self.fg, texture_tag=fgtex, width=zw, height=zh, show=True)

            gui.delete_item(self.bgtex)
            gui.delete_item(self.fgtex)
            self.bgtex = bgtex
            self.fgtex = fgtex