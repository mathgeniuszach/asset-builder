from .globals import *

saves = {}
enhancements = {
    "color": ImageEnhance.Color,
    "contrast": ImageEnhance.Contrast,
    "brightness": ImageEnhance.Brightness,
    "sharpness": ImageEnhance.Sharpness
}

# Maps numbers from the range 0-2 to 0-infinity, where 1 maps to 1
x2x = lambda x: x/(2-x)

def get_filter_image(img: Image.Image, filters: list, checkboxes: dict):
    outimg = img
    for ifilt in filters:
        outimg = apply_filter(outimg, ifilt, checkboxes)
    return outimg

def apply_filter(img: Image.Image, filter: dict, checkboxes: dict):
    # Only apply filter if checkbox is selected
    if "if" in filter:
        if not checkboxes.get(filter["if"], False):
            return img
    
    outimg = img

    # Apply filter based on type
    ftype = filter.get("type")
    try:
        if ftype == "multiple":
            for ifilt in filter.get("filters", []):
                outimg = apply_filter(outimg, ifilt, checkboxes)
        elif ftype == "rebox":
            nimg = Image.new("RGBA", filter["size"])
            nimg.alpha_composite(outimg, tuple(filter["offset"]))
            outimg = nimg
        elif ftype == "resize":
            outimg = outimg.resize(filter["size"], resample=Image.Resampling[filter.get("resample", "NEAREST").upper()])
        elif ftype == "copy":
            outimg.alpha_composite(
                get_filter_image(outimg, filter.get("image", outimg), checkboxes),
                tuple(filter.get("pos", (0, 0)))
            )
        elif ftype == "crop":
            outimg = outimg.crop(filter["box"])
        elif ftype == "erase":
            box = filter["box"]
            emimg = Image.new("RGBA", (box[2]-box[0], box[3]-box[1]))
            outimg.paste(emimg, (box[0], box[1]))
        elif ftype == "save":
            ifilt = filter.get("filters")
            if ifilt:
                saves[filter["id"]] = get_filter_image(outimg, ifilt, checkboxes)
            else:
                saves[filter["id"]] = outimg
        elif ftype == "load":
            nimg = saves.get(filter["id"])
            if nimg:
                outimg = nimg
        elif ftype == "select":
            box = filter["box"]
            nimg = outimg.crop(box)
            outimg.paste(get_filter_image(nimg, filter["filters"], checkboxes), (box[0], box[1]))
        elif ftype == "grayscale":
            outimg = outimg.convert("LA").convert("RGBA")
        elif ftype == "enhance":
            enc = enhancements[filter["mode"].lower()]
            if "level" in filter:
                factor = x2x(min(filter["level"], 1.999999))
            else:
                factor = filter.get("factor", 1)
            outimg = enc(outimg).enhance(factor)
    except Exception:
        log.error(f'Failed to apply inner filter of type "{ftype}"', exc_info=True)

    return outimg