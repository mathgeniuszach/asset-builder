from .globals import *

def wrap_text(*args, **kwargs):
    gui.add_text(*args, **kwargs, wrap=0)

def gap(n):
    for i in range(n):
        gui.add_spacer()

class HelpWindow:
    def __init__(self):
        with gui.window(label="Help", tag="help", width=700, height=500, no_collapse=True, show=False):
            with gui.collapsing_header(label="Overview"):
                wrap_text("Welcome to the Asset Builder, a tool for choosing, recolorizing, and stacking images together of the same type.")
                wrap_text("See Controls for guidance on using the tool.")
                wrap_text("See Packs for guidance on creating asset packs yourself.")
                wrap_text("See Quick Tips for the details that you wouldn't figure out just by playing with the tool.")
                wrap_text("See About for some links.")
            
            with gui.collapsing_header(label="Layout & Controls"):
                wrap_text("The layout and controls of the tool are as follows:")
                gap(4)

                wrap_text("First, you have the menu bar.")
                wrap_text("The File menu allows you to open, save, save as, export, or close out the current tab you are in. Exporting does the same thing as saving, except it doesn't allow you to re-load the image back into the tool.")
                wrap_text("The Options menu will let you disable the prompt to save on closing a tab, turn off autobackup, or change the zoom mode. The Reload button will reload all asset packs from the packs folder.")
                wrap_text("The Packs menu will let you see a list of all the packs you have loaded, or reload all the packs from the packs folder.")
                wrap_text("The Help button is self explanitory.")
                wrap_text("The Discord button will open up a join link for you to join my Discord if you need more specific help.")
                gap(4)

                wrap_text("Second, you have the tab bar. Each project you work on can be separated into distinct, separate tabs. You can press the + button to add a new tab, or the x button to close out the tab you are currently working on. At the start, you should see one tab named * Untitled.")
                gap(4)

                wrap_text("Third, you have below that on the left your image view pane. When you select a type from the pane to the right, an image will appear on the left for you. You can use the zoom controls to zoom in or out, and pan around an image by left-click dragging on it with your mouse.")
                gap(4)

                wrap_text("Finally, you have to the right the type and part selection options.")
                wrap_text("Select a type if you haven't already, and a bunch of options for parts should show up. You can select anything from the dropdown menus, though keep in mind some dropdown menus may have different items depending on others. If there's a + button below a dropdown, that means you can add multiple of that part to the image (click the button to do so).")
                wrap_text("To the right of each dropdown is also up to 4 color selection squares (you must select an item from the dropdown to see at least one), each of which let you change the color of a specific item in the menu.")
                wrap_text("You can increase/decrease Brightness, Contrast, or Sharpness/Blur of a layer of an image, as well as set a colorization mode and color (you must set a color mode to recolorize the part). You can Ctrl+Click on the sliders to set a value directly with your keyboard, and you can right click any square to quickly reset it to the default values.")
            
            with gui.collapsing_header(label="Packs"):
                wrap_text("So your curious about making asset packs, eh?")
                wrap_text("For the best examples, check out the packs that come with the tool. These utilize a large number of the features present in the tool.")

                gap(1)
                with gui.tree_node(label="Format & Metadata"):
                    wrap_text('All packs are either a folder or an archive (.zip or .7z) containing a root level "meta.yaml" file followed by some code. Right now, the "meta.yaml" file doesn\'t do much and just needs to be present for the pack to be detected (If you want, fill in the "name", "desc", and "version" fields with two strings and a number for future versions)')
                    wrap_text('Next to this root meta file are a collection of one or more folders containing assets for a specific "type" that is shown in the Type selection box. Use underscores (instead of spaces) to refer to spaces. Two separate packs may contain the same "type" folder; in that case, the content from that type will be merged (see Load Order & Conflicts for more info)')
                    wrap_text('Each of these "type" folders must contain a meta.yaml file specifying how to load any content that type provides (See Type Metadata for more info).')
                    wrap_text('Next to the type meta file are a collection of part folders (once again, use underscores, not spaces) that are generated as selectable options on parts panel according to the rules in the type meta file. Each folder will have a collection of folders/images AND/OR a meta.yaml file defining how to load the images in that folder (See Parts for more info).')
                
                gap(1)
                with gui.tree_node(label="Type Metadata"):
                    wrap_text('There are 6 main fields in every meta file:')
                    gap(2)

                    wrap_text('First, is the "priority" field. It is optional and defaults to the value 0, and it can take negative and decimal values. Packs with higher priority have their values prioritized over others (that is, their values/images are used in the case of conflicts).')
                    gap(2)

                    wrap_text('Second, is the "size" field, which is a list of two values. These values are the width and height of all images in the pack. If an image does not match the size given, it will not be loaded.')
                    gap(2)

                    wrap_text('Third, is the "checkboxes" field, which is used to generate custom checkboxes that can be used to change how the "filters" and the "draw_order" fields work. Every item in the field is an id followed by a label to use for that checkbox.')
                    gap(2)

                    wrap_text('Fourth, is the "default" field, which specifies default values for parts, checkboxes, or colors.')
                    gap(2)

                    wrap_text('Fifth, is the "draw_order" field, which marks every part in the type with a priority that determines the order to draw that part in. Parts with a smaller priority number end up behind (and are drawn before) parts with a larger priority. It is also possible to use conditional priority based on the value of checkboxes or whether or not a pixel is before or after a horizontal or vertical line (before being left or above). You can put conditional values inside of each other.')
                    gap(2)

                    wrap_text('Sixth, is the "groups" field, which tells the tool what parts (and in what order) to generate as selectable dropdowns on the right side. Each group has an id (sorted alphabetically) that determines what order to load the groups in.')
                    gap(2)

                    wrap_text('Seventh, is the "filters" field, which is a list of post-processing effects you can apply to the image to change it\'s size or something about the image (See Filters for more info). Root level filters additionally have their own "priority" field that is separate from the main one; smaller priority values make the filter be applied first. Priority defaults to 0.')
                    gap(2)

                    wrap_text('Finally, is the "animations" field, which is a list of post-post-processing effects which slice up the image into sections and animate the image. Animations must match a certain size of the image to work properly.')
                
                gap(1)
                with gui.tree_node(label="Parts"):
                    wrap_text('Perhaps the most important part about any pack are the parts. Each part folder may contain both a meta file and either a collection of folders or images that are available as choices in that part field\'s dropdown selector.')
                    wrap_text('The meta file is optional, and does not need to be provided. But it does have a few options. If "disabled" is set to True, that part will not be loaded. If "multiple" is set to True, multiple of that part can be selected in the tool. If "color" is set to a different part, this part will not have it\'s own color options, but leech off of this part instead. If "depends" is set to True, switch to depend mode; otherwise, use normal mode.')
                    gap(2)
                    wrap_text('In normal mode, there should be no sub-folders in the part folder. Rather, all should be images. Each image should be a name in the format "Part_Name.png". To specify additional layers on top of the image (each which can have their own color), use the form "Part_Name overlay.png", "Part_Name overlay2.png" or "Part_Name overlay3.png". There\'s a maximum of 4 layers available.')
                    wrap_text('In depend mode, either use folders or images for each of the part names that you can select in the "depends" type. Inside of each of those folders, refer to "normal" mode. These sub-folders can have meta files, which can only have the "depends" and "color" fields. Note that the "color" field must be present in the same folder as an image to be used there.')
                
                gap(1)
                with gui.tree_node(label="Filters"):
                    wrap_text('Filters (that is, those in the filters field), accept an "if" field that refers to a checkbox that must be set in order to work, as well as a type field and other type-specific fields. Here\'s a list of type fields as well as their type specific fields:')
                    gap(2)

                    wrap_text('The "multiple" filter allows you to specify a collection of sub-filters in the field "filters" to apply in the order given in the list. Each sub-filter does not accept priority values.')
                    gap(2)

                    wrap_text('The "rebox" filter allows you to resize the canvas and crop an image in one go. Specify a new "size" (list of two values, width and height) for the image to have, then provide an "offset" (list of two values, number of pixels right and down from the top left corner to insert the old image into the new canvas). The offset can have negative values. Any pixels that would be drawn outside the image are cropped.')
                    gap(2)

                    wrap_text('The "resize" filter allows you to resize the image to any size. Give it a "size" (list of two values, width and height) to resize to, followed by a "resample" field (defaults to "nearest" if not given) to resize the image with. Resample modes are "nearest", "box", "bilinear", "hamming", "bicubic", and "lanczos".')
                    gap(2)

                    wrap_text('The "copy" filter allows you to take a copy of the image, apply some filters on it, and the paste that filtered image onto the current image at some location. Use the "image" field to list a couple of filters, and the "pos" field to specify a location from the top left corner to paste into.')
                    gap(2)

                    wrap_text('The "crop" filter takes in a single field "box" (list of four values, the left, top, right and bottom pixel values of the bounding box to crop) and crops the image to just that box.')
                    gap(2)

                    wrap_text('The "erase" filter erases part of the image specified by "box" (list of four values, the left, top, right, and bottom pixels).')
                    gap(2)

                    wrap_text('The "select" filter crops a part of the image specified by "box", applies the given "filters" to the cropped image, and then pastes the image (replacing even fully transparent pixels) to it\'s original position.')

                    wrap_text('The "save" and "load" filters go hand in hand; use the "save" filter to save the image in it\'s current state (or provide a list of filters in the "filters" field to apply) to the given "id", then later use the "load" filter to replace the current image with the one saved with the given "id". If an image with that "id" cannot be loaded, this filter will not do anything.')
                    gap(2)

                    wrap_text('The "grayscale" filter converts the image to grayscale.')
                    gap(2)

                    wrap_text('The "enhance" filter applies an enhancement filter to the entire image. Specify a "mode" ("color", "contrast", "brightness", or "sharpness"), then either a "level" (0-2, 1 means do nothing) or a "factor" (0-inf, 1 means do nothing). Negative values might work too.')
                    gap(2)
                
                gap(1)
                with gui.tree_node(label="Load Order & Conflicts"):
                    wrap_text("For maximum extensibility, multiple asset packs can provide assets for the same type; thus, conflicts may occur. In general, packs who mark their types with higher priorities have their values prioritized over others.")
                    gap(4)

                    wrap_text("When considering the type metadata:")
                    wrap_text('"size" is determined from the pack with the highest priority.')
                    wrap_text('"checkboxes" with different ids are all combined together; two checkboxes with the same id use the label from the pack with the highest priority.')
                    wrap_text('"default" values that refer to different fields are combined together; two default values that refer to the same field use the value provided by the pack with the highest priority.')
                    wrap_text('"draw_order" values that refer to different fields are combined together; two different values that refer to the same field use the value provided by the pack with the highest priority.')
                    wrap_text('"groups" with different ids are all merged together. Two groups with the same id are merged together, with the values from the higher priority pack coming first. If you want to disable a part from another pack, use the "disabled: True" field in a part\' metadata')
                    wrap_text('"filters" are applied in the order of their own given priorities. They do not conflict.')
                    gap(4)

                    wrap_text("When considering individual parts:")
                    wrap_text("Folders with the same name are always merged and act as if they are from the same pack.")
                    wrap_text("If an image would end up in the same location as another image, the image from the pack with the highest priority is used.")
                    wrap_text("Part metadata is merged from each pack; if a field is specified in muliple packs, the value from the pack with the highest priority is used.")
                
                gap(1)

            with gui.collapsing_header(label="Quick Tips"):
                wrap_text("Saving an image saves both the image and the options you have selected (so it can be reloaded into the tool), while exporting a file saves only the image (so it cannot be reloaded).")
                wrap_text("You can Ctrl+Click on a slider (like Brightness, etc.) to set it's value directly. You can set some values outside their minimum and maximum this way for interesting effects.")
                wrap_text("Right click on a color box to reset it's settings to the default values.")
                wrap_text("Priority values in a pack can be positive or negative, and also support float values.")
                wrap_text('When you add an asset of a name like "{Asset}_2" into your pack, rename the original "{Asset}" to "{Asset}_1". This will not break compatibility, as internally the names "{Asset}" and "{Asset}_1" are translated into each other. Same thing with "{Asset}_1" and "{Asset}_1A", and "{Asset}_2" and "{Asset}_2A".')
                wrap_text('When non-descriptively naming things in a pack, use numbers first, then capitalized letters. So do "{Asset}_2A" or "{Asset}_2", not "{Asset}_A2". Names like "{Asset}_B" are fine, and mean "{Asset}_1B".')
                wrap_text('Letters only go from A-Z in packs, while numbers up to any value may be used.')
            
            with gui.collapsing_header(label="About"):
                wrap_text("Asset Builder - mathgeniuszach (Zach K)")
                gui.bind_item_theme(
                    gui.add_button(label="Source Code", callback=lambda: webbrowser.open(GITHUB)),
                    G.app.hyper_theme
                )
    
    def show(self):
        gui.show_item("help")