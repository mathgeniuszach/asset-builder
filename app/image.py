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
        self.size = (0, 0)
        self.zoom = 2
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

        with gui.child_window(width=-1, height=-2) as self.cwin:
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

                self.bgtex = gui.add_raw_texture(1, 1, numpy.array([0,0,0,0], dtype=numpy.float32), parent="texreg")
                self.fgtex = gui.add_raw_texture(1, 1, numpy.array([0,0,0,0], dtype=numpy.float32), parent="texreg")
                self.bg = gui.add_image(self.bgtex, pos=(5, 40), parent="imagewin", before="zoombar", show=False)
                self.fg = gui.add_image(self.fgtex, pos=(5, 40), parent="imagewin", before="zoombar", show=False)
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
    
    def update_size(self, zoom, size, data=None):
        w, h = int(size[0]*zoom), int(size[1]*zoom)
        if data is None:
            gui.configure_item(self.bg, show=False)
            gui.configure_item(self.fg, show=False)
        else:
            bgtex = gui.add_raw_texture(w, h, make_checkerboard(w, h).ravel(), parent="texreg")
            fgtex = gui.add_raw_texture(w, h, data, parent="texreg")
            gui.configure_item(self.bg, texture_tag=bgtex, width=w, height=h, show=True)
            gui.configure_item(self.fg, texture_tag=fgtex, width=w, height=h, show=True)

            gui.delete_item(self.bgtex)
            gui.delete_item(self.fgtex)
            self.bgtex = bgtex
            self.fgtex = fgtex
        
        with SAFETY_LOCK:
            self.size = (w, h)
    
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

    def update(self):
        with SAFETY_LOCK:
            zoom = self.zoom
            size = self.size

        # Delete image if different
        if not G.active_type:
            nsize = (0, 0)
        
            if size != nsize:
                self.update_size(zoom, nsize)
            
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
        
        # Save outimg for saving to a file
        self.image = outimg

        # Shrink/grow image to zoom size        
        w = outimg.width
        h = outimg.height
        zw = int(w*zoom)
        zh = int(h*zoom)

        if zoom != 1:
            resample = Image.Resampling.BICUBIC
            if gui.get_value("nearest") and zoom > 1:
                resample = Image.Resampling.NEAREST

            outimg = outimg.resize(
                (zw, zh),
                resample=resample
            )
        
        # Convert img to numpy array
        out = numpy.divide(numpy.array(outimg, dtype=numpy.float32), 255)

        # Update image size if necessary
        if size != (zw, zh):
            self.update_size(zoom, (w, h), out)
        else:
            gui.set_value(self.fgtex, out)
