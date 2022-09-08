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

import bpy
from mathutils import (Color, Vector)

M2P_TEXT_NAME = "m2pText"

uni_attr_default_list = {
    "name": "",
    "label": "",
    "width": 0.0,
    "width_hidden": 42.0,
    "height": 100.0,
    "color": Color((0.608000, 0.608000, 0.608000)),
    "use_custom_color": False,
    "mute": False,
    "hide": False,
}

WRITE_DEFAULTS_UNI_NODE_OPT = "write_defaults"
WRITE_LINKED_DEFAULTS_UNI_NODE_OPT = "write_linked_defaults"
LOC_DEC_PLACES_UNI_NODE_OPT = "loc_decimal_places"
WRITE_ATTR_NAME_UNI_NODE_OPT = "write_attr_name"
WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT = "write_attr_width_height"

FILTER_OUT_ATTRIBS = ['color', 'dimensions', 'height', 'hide', 'inputs', 'internal_links', 'label', 'location',
                         'mute', 'name', 'outputs', 'parent', 'rna_type', 'select', 'show_options', 'show_preview',
                         'show_texture', 'type', 'use_custom_color', 'width', 'width_hidden',
                         'is_active_output', 'interface']

NODES_WITH_WRITE_OUTPUTS = ['ShaderNodeValue', 'ShaderNodeRGB', 'CompositorNodeValue', 'CompositorNodeRGB']

def get_world_shader_name_from_tree(node_tree):
    for w in bpy.data.worlds:
        if w.node_tree == node_tree:
            return w.name
    return None

# add escape characters to backslashes and double-quote chars in given string
def esc_char_string(in_str):
    return in_str.replace('\\', '\\\\').replace('"', '\\"')

def get_input_num_for_link(tr_link):
    for c in range(0, len(tr_link.to_socket.node.inputs)):
        if tr_link.to_socket.node.inputs[c] == tr_link.to_socket:
            return c
    return None

def get_output_num_for_link(tr_link):
    for c in range(0, len(tr_link.from_socket.node.outputs)):
        if tr_link.from_socket.node.outputs[c] == tr_link.from_socket:
            return c
    return None

def bpy_value_to_string(value):
    # write attribute, if it matches a known type
    if isinstance(value, str):
        return "\"%s\"" % value
    elif isinstance(value, bool):
        return "%s" % value
    elif isinstance(value, int):
        return "%d" % value
    elif isinstance(value, float):
        return "%f" % value
    # if attribute has a length then it is a Vector, Color, etc., so write elements of attribute in a tuple
    elif hasattr(value, '__len__'):
        vec_str = ""
        for val_index in range(len(value)):
            if vec_str != "":
                vec_str = vec_str + ", "
            vec_str = vec_str + str(value[val_index])
        return "(" + vec_str + ")"
    # if the attribute's value has attribute 'name', then check if it is in a Blender built-in data list
    elif hasattr(value, 'name'):
        if type(value) == bpy.types.Image:
            return "bpy.data.images.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Mask:
            return "bpy.data.masks.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Scene:
            return "bpy.data.scenes.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Material:
            return "bpy.data.materials.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Object:
            return "bpy.data.objects.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Collection:
            return "bpy.data.collections.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.GeometryNodeTree or type(value) == bpy.types.ShaderNodeTree:
            return "bpy.data.node_groups.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Text:
            return "bpy.data.texts.get(\"" + value.name + "\")"

def write_filtered_attribs(m2p_text, line_prefix, node, ignore_attribs):
    # loop through all attributes of 'node' object
    for attr_name in dir(node):
        # if attribute is in ignore attributes list, then continue to next attribute
        if attr_name in ignore_attribs:
            continue
        # get the attribute's value
        the_attr = getattr(node, attr_name)
        # filter out attributes that are built-ins (Python/Blender), or callable functions, or
        # attributes that are ignored/handled elsewhere
        if attr_name.startswith('__') or attr_name.startswith('bl_') or callable(the_attr) or \
            attr_name in FILTER_OUT_ATTRIBS:
            continue

        # if type is Color Ramp
        if type(the_attr) == bpy.types.ColorRamp:
            m2p_text.write(line_prefix + "node." + attr_name + ".color_mode = \"%s\"\n" % the_attr.color_mode)
            m2p_text.write(line_prefix + "node." + attr_name + ".interpolation = \"%s\"\n" % the_attr.interpolation)
            # remove one element before adding any new elements, leaving the minimum of one element in list
            # (deleting last element causes Blender error, but one elements needs to be deleted in case only 1 is used)
            m2p_text.write(line_prefix + "node." + attr_name + ".elements.remove(" + "node." + attr_name +
                           ".elements[0])\n")
            # add new elements, as needed
            elem_index = -1
            for el in the_attr.elements:
                elem_index = elem_index + 1
                # if writing first element then don't create new element
                if elem_index < 1:
                    m2p_text.write(line_prefix + "elem = node." + attr_name + ".elements[0]\n")
                    m2p_text.write(line_prefix + "elem.position = %f\n" % el.position)
                # else create new element
                else:
                    m2p_text.write(line_prefix + "elem = node." + attr_name + ".elements.new(%f)\n" % el.position)

                m2p_text.write(line_prefix + "elem.color = (%f, %f, %f, %f)\n" %
                               (el.color[0], el.color[1], el.color[2], el.color[3]))
        # if type is Curve Mapping, e.g. nodes Float Curve (Shader), RGB Curve (Shader), Time Curve (Compositor)
        elif type(the_attr) == bpy.types.CurveMapping:
            m2p_text.write(line_prefix + "node." + attr_name + ".use_clip = %s\n" % the_attr.use_clip)
            m2p_text.write(line_prefix + "node." + attr_name + ".clip_min_x = %f\n" % the_attr.clip_min_x)
            m2p_text.write(line_prefix + "node." + attr_name + ".clip_min_y = %f\n" % the_attr.clip_min_y)
            m2p_text.write(line_prefix + "node." + attr_name + ".clip_max_x = %f\n" % the_attr.clip_max_x)
            m2p_text.write(line_prefix + "node." + attr_name + ".clip_max_y = %f\n" % the_attr.clip_max_y)
            m2p_text.write(line_prefix + "node." + attr_name + ".extend = \"%s\"\n" % the_attr.extend)
            # note: Float Curve and Time Curve have 1 curve, RGB curve has 4 curves (C, R, G, B)
            curve_index = -1
            for curve in the_attr.curves:
                curve_index = curve_index + 1

                # addd new points, as needed
                point_index = -1
                for p in curve.points:
                    point_index = point_index + 1
                    # each curve starts with 2 points by default, so write into these points before creating more
                    # (2 points minimum, cannot delete them)
                    if point_index < 2:
                        m2p_text.write(line_prefix + "point = node." + attr_name + ".curves[%d].points[%d]\n" %
                                       (curve_index, point_index))
                        m2p_text.write(line_prefix + "point.location = (%f, %f)\n" % (p.location[0], p.location[1]))
                    # create new point
                    else:
                        m2p_text.write(line_prefix + "point = node." + attr_name + ".curves[%d].points.new(%f, %f)\n" %
                                       (curve_index, p.location[0], p.location[1]))
                    m2p_text.write(line_prefix + "point.handle_type = \"%s\"\n" % p.handle_type)

            # update the view of the mapping (trigger UI update)
            m2p_text.write(line_prefix + "node." + attr_name + ".update()\n")
        # remaining types are String, Integer, Float, etc. (including bpy.types, e.g. bpy.types.Collection)
        else:
            val_str = bpy_value_to_string(the_attr)
            # do not write attributes that have value None
            # e.g. an 'object' attribute, that is set to None to indicate no object
            if val_str != None:
                m2p_text.write(line_prefix + "node." + attr_name + " = " + val_str + "\n")

def create_code_text(context, space_pad, keep_links, make_into_function, delete_existing, use_edit_tree,
                     uni_node_options):
    line_prefix = ""
    if isinstance(space_pad, int):
        line_prefix = " " * space_pad
    elif isinstance(space_pad, str):
        line_prefix = space_pad

    mat = context.space_data
    m2p_text = bpy.data.texts.new(M2P_TEXT_NAME)

    the_tree_to_use = mat.node_tree
    if use_edit_tree:
        the_tree_to_use = mat.edit_tree

    node_group = bpy.data.node_groups.get(the_tree_to_use.name)
    is_tree_node_group = (node_group != None)

    m2p_text.write("# Blender Python script to re-create ")
    if make_into_function:
        # if using Node Group (Shader or Geometry Nodes)
        if is_tree_node_group:
            m2p_text.write("Node Group named \"" + the_tree_to_use.name + "\"\n\nimport bpy\n\n# add nodes and " +
                           "links to node group \ndef add_group_nodes(node_group_name):\n")
        # if using Compositor node tree
        elif the_tree_to_use.bl_idname == 'CompositorNodeTree':
            m2p_text.write("compositor node tree\n\nimport bpy\n\n# add nodes and links to " +
                           "compositor node tree\ndef add_material_nodes(material):\n")
        # using Material node tree
        else:
            m2p_text.write("material named \"" + the_tree_to_use.name + "\"\n\nimport bpy\n\n# add nodes and links " +
                           "to material\ndef add_material_nodes(material):\n")

    if is_tree_node_group:
        m2p_text.write(line_prefix + "# initialize variables\n")
        m2p_text.write(line_prefix + "new_nodes = {}\n")
        m2p_text.write(line_prefix + "new_node_group = bpy.data.node_groups.new(name=node_group_name, type='" +
                       the_tree_to_use.bl_idname + "')\n")
        # get the node group inputs and outputs
        for ng_input in node_group.inputs:
            m2p_text.write(line_prefix + "new_node_group.inputs.new(type='" + ng_input.bl_socket_idname + "', name=\""+
                           ng_input.name + "\")\n")
        for ng_output in node_group.outputs:
            m2p_text.write(line_prefix + "new_node_group.outputs.new(type='" + ng_output.bl_socket_idname +
                           "', name=\"" + ng_output.name + "\")\n")

        m2p_text.write(line_prefix + "tree_nodes = new_node_group.nodes\n")
    else:
        m2p_text.write(line_prefix + "# initialize variables\n")
        m2p_text.write(line_prefix + "new_nodes = {}\n")
        m2p_text.write(line_prefix + "tree_nodes = material.node_tree.nodes\n")

    if delete_existing:
        m2p_text.write(line_prefix + "# delete all nodes\n")
        m2p_text.write(line_prefix + "tree_nodes.clear()\n")
    m2p_text.write("\n" + line_prefix + "# create nodes\n")

    # set parenting order of nodes (e.g. parenting to frames) after creating all the nodes in the tree,
    # so that parent nodes are referenced only after parent nodes are created
    frame_parenting_text = ""
    # write info about the individual nodes
    for tree_node in the_tree_to_use.nodes:
        m2p_text.write(line_prefix + "node = tree_nodes.new(type=\"%s\")\n" % tree_node.bl_idname)
        ignore_attribs = []
        for attr in uni_attr_default_list:
            # Input Color node will write this value, so ignore it for now
            if tree_node.bl_idname == 'FunctionNodeInputColor' and attr == 'color':
                continue
            if hasattr(tree_node, attr):
                gotten_attr = getattr(tree_node, attr)
                # if write defaults is not enabled, and a default value is found, then skip the default value
                if not uni_node_options[WRITE_DEFAULTS_UNI_NODE_OPT] and gotten_attr == uni_attr_default_list[attr]:
                    continue
                # if not writing 'name' then skip
                elif attr == 'name' and uni_node_options[WRITE_ATTR_NAME_UNI_NODE_OPT] == False:
                    continue
                # if not writing width and height then skip
                elif (attr == 'width' or attr == 'height') and \
                        uni_node_options[WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT] == False:
                    continue

                m2p_text.write(line_prefix + "node." + attr + " = " + bpy_value_to_string(gotten_attr) + "\n")

        # node with parent is special, this node is offset by their parent frame's location
        parent_loc = Vector((0, 0))
        if tree_node.parent != None:
            parent_loc = tree_node.parent.location

        # do rounding of location values, if needed, and write the values
        precision = uni_node_options[LOC_DEC_PLACES_UNI_NODE_OPT]
        loc_x = tree_node.location.x + parent_loc.x
        loc_y = tree_node.location.y + parent_loc.y
        m2p_text.write(line_prefix + "node.location = (%0.*f, %0.*f)\n" % (precision, loc_x, precision, loc_y))

        # Input Color, this attribute is special because this node type's Color attribute is swapped - very strange!
        # (maybe a dinosaur left over from old versions of Blender)
        if tree_node.bl_idname == 'FunctionNodeInputColor':
            m2p_text.write(line_prefix + "node.color = " + bpy_value_to_string(tree_node.color) + "\n")
            ignore_attribs.append("color")

        write_filtered_attribs(m2p_text, line_prefix, tree_node, ignore_attribs)

        # get node input(s) default value(s), each input might be [ float, (R, G, B, A), (X, Y, Z), shader ]
        # TODO: this part needs more testing re: different node input default value(s) and type(s)
        input_count = -1
        for node_input in tree_node.inputs:
            input_count = input_count + 1
            if node_input.hide_value:
                continue
            # ignore virtual sockets and shader sockets, no default
            if node_input.bl_idname == 'NodeSocketVirtual' or node_input.bl_idname == 'NodeSocketShader':
                continue
            # if node doesn't have attribute 'default_value', then cannot save the value - so continue
            if not hasattr(node_input, 'default_value'):
                continue
            # if 'do not write linked default values', and this input socket is linked then skip
            if uni_node_options[WRITE_LINKED_DEFAULTS_UNI_NODE_OPT] == False and node_input.is_linked:
                continue

            m2p_text.write(line_prefix + "node.inputs[" + str(input_count) + "].default_value = (" +
                           bpy_value_to_string(node_input.default_value) + ")\n")

        # get node output(s) default value(s), each output might be [ float, (R, G, B, A), (X, Y, Z), shader ]
        # TODO: this part needs more testing re: different node output default value(s) and type(s)
        output_count = -1
        for node_output in tree_node.outputs:
            output_count = output_count + 1
            if tree_node.bl_idname not in NODES_WITH_WRITE_OUTPUTS:
                continue
            # ignore virtual sockets and shader sockets, no default
            if node_output.bl_idname == 'NodeSocketVirtual' or node_output.bl_idname == 'NodeSocketShader':
                continue
            # if node doesn't have attribute 'default_value', then cannot save the value - so continue
            if not hasattr(node_output, 'default_value'):
                continue
            # if 'do not write linked default values', and this output socket is used (i.e. 'linked'),
            # and it is not a Input Value node, then skip
            if uni_node_options[WRITE_LINKED_DEFAULTS_UNI_NODE_OPT] == False and node_output.is_linked:
                continue

            m2p_text.write(line_prefix + "node.outputs[" + str(output_count) + "].default_value = (" +
                           bpy_value_to_string(node_output.default_value) + ")\n")

        m2p_text.write(line_prefix + "new_nodes[\"" + tree_node.name + "\"] = node\n\n")
        # save a reference to parent node for later, if parent node exists
        if tree_node.parent != None:
            frame_parenting_text = frame_parenting_text + line_prefix + "new_nodes[\"" + tree_node.name + \
                "\"].parent = new_nodes[\"" + tree_node.parent.name + "\"]\n"

    # do node parenting if needed
    if frame_parenting_text != "":
        m2p_text.write(line_prefix + "# parenting of nodes\n" + frame_parenting_text + "\n")

    m2p_text.write(line_prefix + "# create links\n")
    if keep_links:
        m2p_text.write(line_prefix + "new_links = []\n")
    if is_tree_node_group:
        m2p_text.write(line_prefix + "tree_links = new_node_group.links\n")
    else:
        m2p_text.write(line_prefix + "tree_links = material.node_tree.links\n")
    for tree_link in the_tree_to_use.links:
        flint = ""
        if keep_links:
            flint = "link = "
        m2p_text.write(line_prefix + flint + "tree_links.new(new_nodes[\"" + tree_link.from_socket.node.name +
            "\"].outputs[" + str(get_output_num_for_link(tree_link)) + "], new_nodes[\"" +
            tree_link.to_socket.node.name + "\"].inputs[" + str(get_input_num_for_link(tree_link)) + "])\n")
        if keep_links:
            m2p_text.write(line_prefix + "new_links.append(link)\n")
    if make_into_function:
        world_shader_name = get_world_shader_name_from_tree(the_tree_to_use)
        # if using nodes in a group (Shader or Geometry Nodes)
        if is_tree_node_group:
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to new Node Group\n" +
                           "add_group_nodes('" + the_tree_to_use.name + "')\n")
        # if using Compositor node tree
        elif the_tree_to_use.bl_idname == 'CompositorNodeTree':
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to compositor node tree\n" +
                           "add_material_nodes(bpy.context.scene)\n")
        # if using World shader node tree
        elif world_shader_name != None:
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to the World shader\n" +
                           "world_shader = bpy.data.worlds.new(\""+world_shader_name+"\")\n" +
                           "world_shader.use_nodes = True\n" +
                           "add_material_nodes(world_shader)\n")
        # else using Material Shader Nodes
        else:
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to the active material " +
                           "of the active object\nobj = bpy.context.active_object\n" +
                           "if obj != None and obj.active_material != None:\n" +
                           "    add_material_nodes(obj.active_material)\n")
    # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
    # TODO: fix this, not working in Blender 3.1
    m2p_text.current_line_index = 0

class M2P_CreateText(bpy.types.Operator):
    """Make Python text-block from current Material/Geometry node tree"""
    bl_idname = "mat2py.awesome"
    bl_label = "Nodes 2 Python"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        s = context.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ('CompositorNodeTree', 'ShaderNodeTree', 'TextureNodeTree', 'GeometryNodeTree'):
            return True
        return False

    def execute(self, context):
        scn = context.scene
        uni_node_options = {
            LOC_DEC_PLACES_UNI_NODE_OPT: scn.M2P_WriteLocDecimalPlaces,
            WRITE_DEFAULTS_UNI_NODE_OPT: scn.M2P_WriteDefaultValues,
            WRITE_LINKED_DEFAULTS_UNI_NODE_OPT: scn.M2P_WriteLinkedDefaultValues,
            WRITE_ATTR_NAME_UNI_NODE_OPT: scn.M2P_WriteAttribName,
            WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT: scn.M2P_WriteAttribWidthAndHeight,
        }
        create_code_text(context, scn.M2P_NumSpacePad, scn.M2P_KeepLinks, scn.M2P_MakeFunction, scn.M2P_DeleteExisting,
            scn.M2P_UseEditTree, uni_node_options)
        return {'FINISHED'}
