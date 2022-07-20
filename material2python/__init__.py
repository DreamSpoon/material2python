# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Material 2 Python",
    "description": "Convert material/geometry nodes to Python text-block.",
    "author": "Dave",
    "version": (0, 2, 1),
    "blender": (2, 80, 0),
    "location": "Material Shader Nodes / Geometry Shader Nodes",
    "category": "Developer",
}

import bpy as boop
from .mat2py import Mat2Python

if boop.app.version < (2,80,0):
    Region = "TOOLS"
else:
    Region = "UI"

class M2P_MaterialToPython(boop.types.Panel):
    bl_idname = "NODE_PT_material2python"
    bl_label = "Mat2Python"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = Region
    bl_category = "Mat2Python"

    def draw(self, fun):
        layout = self.layout
        box = layout.box()
        box.label(text="Great Stuff")
        box.operator("major.awesome")
        box.prop(fun.scene, "M2P_NumSpacePad")
        box.prop(fun.scene, "M2P_KeepLinks")
        box.prop(fun.scene, "M2P_MakeFunction")
        box.prop(fun.scene, "M2P_DeleteExisting")
        box.prop(fun.scene, "M2P_UseEditTree")

def register():
    boop.utils.register_class(Mat2Python)
    boop.utils.register_class(M2P_MaterialToPython)

    bts = boop.types.Scene
    bp = boop.props
    bts.M2P_NumSpacePad = bp.IntProperty(name="Num Space Pad", description="Number of spaces to prepend to each " +
        "line of code output in text-block", default=4, min=0)
    bts.M2P_KeepLinks = bp.BoolProperty(name="Keep Links", description="Add created links to a list variable",
        default=True)
    bts.M2P_MakeFunction = bp.BoolProperty(name="Make into Function", description="Add lines of python code to " +
        "create runnable script (instead of just the bare essential code)", default=True)
    bts.M2P_DeleteExisting = bp.BoolProperty(name="Delete Existing Shader",
        description="Include code in the output that deletes all nodes in Shader Material / Geometry Node Setup before creating new nodes", default=True)
    bts.M2P_UseEditTree = bp.BoolProperty(name="Use Edit Tree",
        description="Use node tree currently displayed (edit_tree) in the Shader node editor. To capture custom " +
            "Node Group, enable this option and use 'Material to Python' button while viewing the custom Node Group",
            default=True)

def unregister():
    boop.utils.unregister_class(Mat2Python)
    boop.utils.unregister_class(M2P_MaterialToPython)

if __name__ == "__main__":
    register()
