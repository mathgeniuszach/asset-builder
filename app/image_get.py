from .globals import *

# Maps numbers from the range 0-2 to 0-infinity, where 1 maps to 1
x2x = lambda x: x/(2-x)

def get_pnum(p, item, size):
    if isinstance(p, dict):
        # Conditional priority
        try:
            ptype = p["type"]
            if ptype == "checkbox":
                # Checkbox changes priority
                if G.active["checkboxes"].get(p["id"], False):
                    return get_pnum(p["true"], item, size)
                else:
                    return get_pnum(p["false"], item, size)
            elif ptype == "cut_v" or ptype == "cut_h":
                # Cut image into boxes based on line
                before = get_pnum(p["before"], item, size)
                after = get_pnum(p["after"], item, size)
                
                out = []
                if ptype == "cut_v":
                    # Cut vertically
                    x = p["x"]
                    if type(before) == list:
                        for p_box in before:
                            # Shift right to furthest left
                            p_box[1][2] = min(p_box[1][2], x)
                            out.append(p_box)
                    else:
                        out.append((before, [0, 0, x, size[1]]))
                    if type(after) == list:
                        for p_box in after:
                            # Shift left to furthest right
                            p_box[1][0] = max(p_box[1][0], x)
                            out.append(p_box)
                    else:
                        out.append((after, [x, 0, size[0], size[1]]))
                else:
                    # Cut horizontally
                    y = p["y"]
                    if type(before) == list:
                        for p_box in before:
                            # Shift down to furthest up
                            p_box[1][3] = min(p_box[1][3], y)
                            out.append(p_box)
                    else:
                        out.append((before, [0, 0, size[0], y]))
                    if type(after) == list:
                        for p_box in after:
                            # Shift up to furthest down
                            p_box[1][1] = max(p_box[1][1], y)
                            out.append(p_box)
                    else:
                        out.append((after, [0, y, size[0], size[1]]))
                
                return out
        except Exception:
            log.error(f'Invalid priority conditional for "{item}", assuming -1')
            return -1
    else:
        # Just a number
        return p

def colorize_image(image: Image.Image, color):
    if not color: return image.convert("RGBA")

    outimg = image

    # Determine whether or not to grayscale image
    mode = color.get("mode", "?")
    if mode == "x" or mode == "+":
        outimg = outimg.convert("LA")
        gray = True
    else:
        outimg = outimg.convert("RGBA")
        gray = False

    # Shift image contrast
    contrast = min(color.get("contrast", 1), 1.999999) # Exact 2 would lead to zero division error
    if contrast != 1:
        outimg = ImageEnhance.Contrast(outimg).enhance(x2x(contrast))
    
    # Shift image sharpness
    sharpness = min(color.get("sharpness", 1), 1.999999) # Exact 2 would lead to zero division error
    if sharpness != 1:
        if sharpness > 1:
            # Sharpness greater than 1 slopes off to infinity
            outimg = ImageEnhance.Sharpness(outimg).enhance(x2x(sharpness))
        else:
            # Because "perfect" blur of 0 sharpness isn't really blurry enough,
            # We apply blur in "steps". More than 2000 steps is overkill though.
            if sharpness >= 0:
                v = 1-sharpness
                mid = 0
                
                step = 1 / min(max(1, color.get("blur_steps", 1)), 2000)
                while v > step:
                    outimg = ImageEnhance.Sharpness(outimg).enhance(mid)
                    v -= step
                outimg = ImageEnhance.Sharpness(outimg).enhance(1-v/step)
            else:
                # Negative sharpness should preserve some weird properties.
                v = abs(sharpness)
                step = v / min(max(1, color.get("blur_steps", 1)), 2000)
                while v > step:
                    outimg = ImageEnhance.Sharpness(outimg).enhance(sharpness)
                    v -= step
                outimg = ImageEnhance.Sharpness(outimg).enhance(-v)

    # Shift image brightness (correctly)
    brightness = color.get("brightness", 0)
    if brightness != 0:
        a = numpy.array(outimg, dtype=numpy.int16)

        if gray:
            a[:,:,0] += brightness
            outimg = Image.fromarray(numpy.clip(a, 0, 255).astype(numpy.uint8), "LA")
        else:
            a[:,:,:3] += brightness
            outimg = Image.fromarray(numpy.clip(a, 0, 255).astype(numpy.uint8), "RGBA")
    
    # Color shift image
    if mode != "?":
        color = color.get("color", (128, 128, 128))
        if mode == "x" or mode == "X":
            a = numpy.array(outimg.convert("RGBA"), dtype=numpy.int32)
            a[:,:,0] *= int(color[0])
            a[:,:,1] *= int(color[1])
            a[:,:,2] *= int(color[2])
            a[:,:,:3] //= 255
        elif mode == "+" or mode == "A":
            a = numpy.array(outimg.convert("RGBA"), dtype=numpy.int16)
            a[:,:,0] += int(color[0] - 128)
            a[:,:,1] += int(color[1] - 128)
            a[:,:,2] += int(color[2] - 128)
        
        outimg = Image.fromarray(numpy.clip(a, 0, 255).astype(numpy.uint8), "RGBA")
    
    return outimg.convert("RGBA")

def get_im(part, k):
    if k is None: return None
    return part.get(k) or part.get(k + "_1") or part.get("_")

def get_image(parts, item):
    active = G.active["parts"]
    acolor = G.active["colors"]
    part = parts[item]

    if item not in active and not part["/depends"]: return

    # Handle dependencies
    # TODO: Make this support branching dependencies
    prevpart = None
    for ditem in part["/depends"]:
        # Handle the wackos who depend on multi-values
        k = active.get(ditem, "_")
        if type(k) == list: k = k[0]

        prevpart = part
        part = get_im(part, k)
        if part is None:
            return None

    # Handle THIS value (and also colorize image)
    sel = active.get(item, None)

    # Use either the color from the marked colorpart, or the item itself.
    if not isinstance(part, dict):
        colorpart = prevpart.get("/meta", {}).get("color")
    else:
        colorpart = part.get("/meta", {}).get("color")
    col = acolor.get(colorpart or item, {})

    if type(sel) == list:
        # Multiple images
        out = []
        if isinstance(part, Image.Image):
            # Single layer, image of dependency
            for icol in col:
                out.append(colorize_image(part, icol[0]))
        elif type(part) == list:
            # Multiple layers, image of dependency
            for icol in col:
                out.append(tuple(colorize_image(ip, c) for ip, c in zip(part, col)))
        else:
            for i, icol in zip(sel, col):
                p = get_im(part, i)
                if p:
                    if type(p) == list:
                        # Multiple layers, multiple colors
                        for ip, c in zip(p, icol):
                            out.append(colorize_image(ip, c))
                    else:
                        # Single layer, single color
                        out.append(colorize_image(p, icol[0]))
        
        return tuple(out)
    else:
        # Single image
        if isinstance(part, Image.Image):
            # Single layer, image of dependency
            return colorize_image(part, col[0])
        elif type(part) == list:
            # Multiple layers, image of dependency
            return tuple(colorize_image(ip, c) for ip, c in zip(part, col))
        else:
            p = get_im(part, sel)
            if p:
                if type(p) == list:
                    # Multiple layers, multiple colors
                    return tuple(colorize_image(ip, c) for ip, c in zip(p, col))
                else:
                    # Single layer, single color
                    return colorize_image(p, col[0])
    
    return None