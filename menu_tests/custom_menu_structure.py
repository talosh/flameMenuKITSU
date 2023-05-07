################################################################################
#
# Filename: custom_menu_structure.py
#
# Copyright (c) 2022 Autodesk, Inc.
# All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
################################################################################

"""
Examples of how you can define two different menu structures for the same custom actions.
"""

def get_batch_custom_ui_actions():
    import flame

    cursor = flame.batch.cursor_position

    def scope_schematic(selection):
        '''This scoping makes the menu/actions appear when you click in the background of a Batch Schematic.'''
        return len(selection) == 0

    def add_render(selection):
        render = flame.batch.create_node("Render")
        render.pos_x = cursor[0]
        render.pos_y = cursor[1]

    def add_write(selection):
        write = flame.batch.create_node("Write File")
        write.pos_x = cursor[0]
        write.pos_y = cursor[1]

    def add_resize(selection):
        resize = flame.batch.create_node("Resize")
        resize.pos_x = cursor[0]
        resize.pos_y = cursor[1]

    def add_mono(selection):
        mono = flame.batch.create_node("Mono")
        mono.pos_x = cursor[0]
        mono.pos_y = cursor[1]

    return [
        # The following will create the pre-2023.2 Update structure for your functions.
        # The hierarchy, order, and separator attributes must not be set.
        # Make sure that maximumVersion is set at 2023.1.0.0 for all actions.
        {
           "name": "Examples / Add Nodes",
           "actions": [
                {
                    "name": "Add Resize",
                    "isVisible": scope_schematic,
                    "maximumVersion": "2023.1.0.0",
                    "execute": add_resize
                },
                {
                    "name": "Add Mono",
                    "isVisible": scope_schematic,
                    "maximumVersion": "2023.1.0.0",
                    "execute": add_mono
                },
                {
                    "name": "Add Render",
                    "isVisible": scope_schematic,
                    "maximumVersion": "2023.1.0.0",
                    "execute": add_render
                },
                {
                    "name": "Add Write",
                    "isVisible": scope_schematic,
                    "maximumVersion": "2023.1.0.0",
                    "execute": add_write
                }
           ]
        },
        # This structure calls the same functions as above but uses the new features available in 2023.2 Update.
        # You can use hierarchy, order, and separator attributes.
        # Make sure that minimumVersion is set at 2023.2.0.0 for all actions.
        {
           # This entry creates a submenu at the first level of a contextual menu.
           # There is no action specified because we are only creating the submenu to be used for the hierarchy later on.
           "name": "Example / Add Nodes",
           "hierarchy": [],
           "actions": [
           ]
        },
        {
           # This entry adds two custom actions in a Tools submenu.
           # hierarchy is used to put the Tools submenu inside the Add Nodes submenu defined above.
           # order is used to enforce in which order the different submenus and actions will be displayed.
           # separator is used to add a separator below the Tools submenu. They can also be added between actions.
           "name": "Tools",
           "hierarchy": ["Example / Add Nodes"],
           "order": 1,
           "separator": "below",
           "actions": [
                {
                    "name": "Add Resize",
                    "order": 1,
                    "isVisible": scope_schematic,
                    "minimumVersion": "2023.2.0.0",
                    "execute": add_resize
                },
                {
                    "name": "Add Mono",
                    "order": 2,
                    "isVisible": scope_schematic,
                    "minimumVersion": "2023.2.0.0",
                    "execute": add_mono
                }
           ]
        },
        {
           # This entry adds another submenu inside the Add Nodes submenu.
           "name": "Outputs",
           "hierarchy": ["Example / Add Nodes"],
           "order": 2,
           "actions": [
                {
                    "name": "Add Render",
                    "order": 1,
                    "isVisible": scope_schematic,
                    "minimumVersion": "2023.2.0.0",
                    "execute": add_render
                },
                {
                    "name": "Add Write File",
                    "order": 2,
                    "isVisible": scope_schematic,
                    "minimumVersion": "2023.2.0.0",
                    "execute": add_write
                }
           ]
        }
    ]
