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
    "color": Color((0.608, 0.608, 0.608)),
    "use_custom_color": False,
    "mute": False,
    "hide": False,
    "select": None,
}

WRITE_DEFAULTS_UNI_NODE_OPT = "write_defaults"
WRITE_LINKED_DEFAULTS_UNI_NODE_OPT = "write_linked_defaults"
LOC_DEC_PLACES_UNI_NODE_OPT = "loc_decimal_places"
WRITE_ATTR_NAME_UNI_NODE_OPT = "write_attr_name"
WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT = "write_attr_width_height"
WRITE_ATTR_SELECT_UNI_NODE_OPT = "write_attr_select"

FILTER_OUT_ATTRIBS = ['color', 'dimensions', 'height', 'hide', 'inputs', 'internal_links', 'label', 'location',
                         'mute', 'name', 'outputs', 'parent', 'rna_type', 'select', 'show_options', 'show_preview',
                         'show_texture', 'type', 'use_custom_color', 'width', 'width_hidden',
                         'is_active_output', 'interface']

NODES_WITH_WRITE_OUTPUTS = ['ShaderNodeValue', 'ShaderNodeRGB', 'CompositorNodeValue', 'CompositorNodeRGB']

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
    # if attribute has a length then it is a Vector, Color, etc., so write elements of attribute in a tuple,
    # unless it is a set
    elif hasattr(value, '__len__'):
        vec_str = ""
        # is it a set?
        if isinstance(value, set):
            for item in value:
                if vec_str != "":
                    vec_str = vec_str + ", "
                if isinstance(item, str):
                    vec_str = vec_str + "\"" + str(item) + "\""
                else:
                    vec_str = vec_str + str(item)
            return "{" + vec_str + "}"
        else:
            for val_index in range(len(value)):
                if vec_str != "":
                    vec_str = vec_str + ", "
                if isinstance(value[val_index], str):
                    vec_str = vec_str + "\"" + str(value[val_index]) + "\""
                else:
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
    # return None, because attribute type is unknown
    else:
        return None

def bpy_compare_to_value(blender_value, va):
    if hasattr(blender_value, '__len__') and hasattr(va, '__len__'):
        # False if lengths of objects are different
        if len(blender_value) != len(va):
            return False
        # is it a set?
        if isinstance(blender_value, set):
            c = 0
            for item in blender_value:
                if item != va[c]:
                    return False
                c = c + 1
        else:
            for val_index in range(len(blender_value)):
                if blender_value[val_index] != va[val_index]:
                    return False
        return True
    else:
        return blender_value == va

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

            # reset the clipping view
            m2p_text.write(line_prefix + "node." + attr_name + ".reset_view()\n")
            # update the view of the mapping (trigger UI update)
            m2p_text.write(line_prefix + "node." + attr_name + ".update()\n")
        # remaining types are String, Integer, Float, etc. (including bpy.types, e.g. bpy.types.Collection)
        else:
            val_str = bpy_value_to_string(the_attr)
            # do not write attributes that have value None
            # e.g. an 'object' attribute, that is set to None to indicate no object
            if val_str != None:
                m2p_text.write(line_prefix + "node." + attr_name + " = " + val_str + "\n")

def get_node_io_value_str(node_io_element, write_linked):
    # ignore virtual sockets and shader sockets, no default
    if node_io_element.bl_idname == 'NodeSocketVirtual' or node_io_element.bl_idname == 'NodeSocketShader':
        return None
    # if node doesn't have attribute 'default_value', then cannot save the value - so continue
    if not hasattr(node_io_element, 'default_value'):
        return None
    # if 'do not write linked default values', and this input socket is linked then skip
    if not write_linked and node_io_element.is_linked:
        return None
    return bpy_value_to_string(node_io_element.default_value)

def create_code_text(context, space_pad, keep_links, make_into_function, delete_existing, ng_output_min_max_def,
                     uni_node_options):
    line_prefix = ""
    if isinstance(space_pad, int):
        line_prefix = " " * space_pad
    elif isinstance(space_pad, str):
        line_prefix = space_pad

    mat = context.space_data
    m2p_text = bpy.data.texts.new(M2P_TEXT_NAME)

    node_group = bpy.data.node_groups.get(mat.edit_tree.name)
    is_tree_node_group = (node_group != None)

    m2p_text.write("# Python script from Blender version " + str(bpy.app.version) + " to create ")
    # if using Node Group (Shader or Geometry Nodes)
    if is_tree_node_group:
        if mat.edit_tree.type == 'GEOMETRY':
            m2p_text.write("Geometry Nodes node group named " + mat.edit_tree.name + "\n\n")
        else:
            m2p_text.write("Shader Nodes node group named " + mat.edit_tree.name + "\n\n")
        if make_into_function:
            m2p_text.write("import bpy\n\n" +
                           "# add nodes and links to node group\n" +
                           "def add_group_nodes(node_group_name):\n")
    # if using Compositor node tree
    elif mat.edit_tree.bl_idname == 'CompositorNodeTree':
        m2p_text.write("Compositor node tree\n\n")
        if make_into_function:
            m2p_text.write("import bpy\n\n" +
                           "# add nodes and links to compositor node tree\n" +
                           "def add_shader_nodes(material):\n")
    # using Material node tree
    else:
        # check if World or Object material
        if bpy.data.worlds.get(mat.id.name):
            m2p_text.write("World Material named " + mat.id.name + "\n\n")
        elif bpy.data.linestyles.get(mat.id.name):
            m2p_text.write("Linestyle Material named " + mat.id.name + "\n\n")
        else:
            m2p_text.write("Object Material named " + mat.id.name + "\n\n")
        if make_into_function:
            m2p_text.write("import bpy\n\n" +
                           "# add nodes and links to material\n" +
                           "def add_shader_nodes(material):\n")

    if is_tree_node_group:
        m2p_text.write(line_prefix + "# initialize variables\n")
        m2p_text.write(line_prefix + "new_nodes = {}\n")
        m2p_text.write(line_prefix + "new_node_group = bpy.data.node_groups.new(name=node_group_name, type='" +
                       mat.edit_tree.bl_idname + "')\n")
        m2p_text.write("\n" + line_prefix + "# remove old group inputs and outputs\n")
        m2p_text.write(line_prefix + "new_node_group.inputs.clear()\n")
        m2p_text.write(line_prefix + "new_node_group.outputs.clear()\n")
        if len(node_group.inputs) > 0 or len(node_group.outputs) > 0:
            m2p_text.write(line_prefix + "# create new group inputs and outputs\n")
        # write group inputs
        for ng_input in node_group.inputs:
            # collect lines to be written before writing, to allow for checking if input attributes need to be written
            lines_to_write = []
            # check/write the min, max, default, and 'hide value' data
            if hasattr(ng_input, "min_value") and ng_input.min_value != -340282346638528859811704183484516925440.0:
                lines_to_write.append(line_prefix + "new_input.min_value = " + bpy_value_to_string(ng_input.min_value) +
                                      "\n")
            if hasattr(ng_input, "max_value") and ng_input.max_value != 340282346638528859811704183484516925440.0:
                lines_to_write.append(line_prefix + "new_input.max_value = " + bpy_value_to_string(ng_input.max_value) +
                                      "\n")
            if hasattr(ng_input, "default_value") and ng_input.default_value != None and \
                    ng_input.default_value != 0.0 and \
                    not bpy_compare_to_value(ng_input.default_value, (0.0, 0.0, 0.0)) and \
                    not ( ng_input.bl_socket_idname == 'NodeSocketColor' and \
                          bpy_compare_to_value(ng_input.default_value, (0.0, 0.0, 0.0, 1.0)) ):
                lines_to_write.append(line_prefix + "new_input.default_value = " +
                                      bpy_value_to_string(ng_input.default_value) + "\n")
            if ng_input.hide_value:
                lines_to_write.append(line_prefix + "new_input.hide_value = True\n")
            # create new_input variable only if necessary, i.e. if input attribute values differ from default values
            if len(lines_to_write) > 0:
                m2p_text.write(line_prefix + "new_input = new_node_group.inputs.new(type='" +
                               ng_input.bl_socket_idname + "', name=\"" + ng_input.name + "\")\n")
                for l in lines_to_write:
                    m2p_text.write(l)
            else:
                m2p_text.write(line_prefix + "new_node_group.inputs.new(type='" + ng_input.bl_socket_idname +
                               "', name=\"" + ng_input.name + "\")\n")
        # write group outputs
        for ng_output in node_group.outputs:
            # collect lines to be written before writing, to allow for checking if input attributes need to be
            # written
            lines_to_write = []
            # write values for node group output min/max/default if needed
            if ng_output_min_max_def:
                # check/write the min, max, default, and 'hide value' data
                if hasattr(ng_output, "min_value") and ng_output.min_value !=-340282346638528859811704183484516925440.0:
                    lines_to_write.append(line_prefix + "new_output.min_value = " +
                                          bpy_value_to_string(ng_output.min_value) + "\n")
                if hasattr(ng_output, "max_value") and ng_output.max_value != 340282346638528859811704183484516925440.0:
                    lines_to_write.append(line_prefix + "new_output.max_value = " +
                                          bpy_value_to_string(ng_output.max_value) + "\n")
                if hasattr(ng_output, "default_value")and ng_output.default_value != None and \
                        ng_output.default_value != 0.0 and \
                        not bpy_compare_to_value(ng_output.default_value, (0.0, 0.0, 0.0)) and \
                        not ( ng_output.bl_socket_idname == 'NodeSocketColor' and \
                              bpy_compare_to_value(ng_output.default_value, (0.0, 0.0, 0.0, 1.0)) ):
                    lines_to_write.append(line_prefix + "new_output.default_value = " +
                                   bpy_value_to_string(ng_output.default_value) + "\n")
            if ng_output.hide_value:
                lines_to_write.append(line_prefix + "new_output.hide_value = True\n")
            if hasattr(ng_output, "attribute_domain") and ng_output.attribute_domain != "POINT":
                lines_to_write.append(line_prefix + "new_output.attribute_domain = '" + ng_output.attribute_domain+
                                      "'\n")
            if hasattr(ng_output, "default_attribute_name") and ng_output.default_attribute_name != "":
                lines_to_write.append(line_prefix + "new_output.default_attribute_name = " +
                                      ng_output.default_attribute_name + "\n")
            # create new_output variable only if necessary, i.e. if output attribute values differ from default
            # values
            if len(lines_to_write) > 0:
                m2p_text.write(line_prefix + "new_output = new_node_group.outputs.new(type='" +
                               ng_output.bl_socket_idname + "', name=\"" + ng_output.name + "\")\n")
                for l in lines_to_write:
                    m2p_text.write(l)
            else:
                m2p_text.write(line_prefix + "new_node_group.outputs.new(type='" + ng_output.bl_socket_idname +
                               "', name=\"" + ng_output.name + "\")\n")

        m2p_text.write(line_prefix + "tree_nodes = new_node_group.nodes\n")
    else:
        m2p_text.write(line_prefix + "# initialize variables\n")
        m2p_text.write(line_prefix + "new_nodes = {}\n")
        m2p_text.write(line_prefix + "tree_nodes = material.node_tree.nodes\n")

    if delete_existing:
        m2p_text.write("\n" + line_prefix + "# delete all nodes\n")
        m2p_text.write(line_prefix + "tree_nodes.clear()\n")
    m2p_text.write("\n" + line_prefix + "# create nodes\n")

    # set parenting order of nodes (e.g. parenting to frames) after creating all the nodes in the tree,
    # so that parent nodes are referenced only after parent nodes are created
    frame_parenting_text = ""
    # write info about the individual nodes
    for tree_node in mat.edit_tree.nodes:
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
                # if not writing select state then skip
                elif attr == 'select' and uni_node_options[WRITE_ATTR_SELECT_UNI_NODE_OPT] == False:
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
            value_str = get_node_io_value_str(node_input, uni_node_options[WRITE_LINKED_DEFAULTS_UNI_NODE_OPT])
            if value_str != None:
                m2p_text.write(line_prefix+"node.inputs["+str(input_count)+"].default_value = "+value_str+"\n")

        # get node output(s) default value(s), each output might be [ float, (R, G, B, A), (X, Y, Z), shader ]
        # TODO: this part needs more testing re: different node output default value(s) and type(s)
        output_count = -1
        for node_output in tree_node.outputs:
            output_count = output_count + 1
            if tree_node.bl_idname not in NODES_WITH_WRITE_OUTPUTS:
                continue
            # always write the value, even if linked, because this node is special
            value_str = get_node_io_value_str(node_output, True)
            if value_str != None:
                m2p_text.write(line_prefix+"node.outputs["+str(output_count)+"].default_value = "+value_str+"\n")

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
    for tree_link in mat.edit_tree.links:
        flint = ""
        if keep_links:
            flint = "link = "
        m2p_text.write(line_prefix + flint + "tree_links.new(new_nodes[\"" + tree_link.from_socket.node.name +
            "\"].outputs[" + str(get_output_num_for_link(tree_link)) + "], new_nodes[\"" +
            tree_link.to_socket.node.name + "\"].inputs[" + str(get_input_num_for_link(tree_link)) + "])\n")
        if keep_links:
            m2p_text.write(line_prefix + "new_links.append(link)\n")

    m2p_text.write("\n" + line_prefix + "# deselect all new nodes\n" +
                   line_prefix + "for n in new_nodes.values(): n.select = False\n")

    if is_tree_node_group:
        m2p_text.write("\n" + line_prefix + "return new_node_group\n")
    else:
        m2p_text.write("\n" + line_prefix + "return new_nodes\n")

    # add function call, if needed
    if make_into_function:
        # if using nodes in a group (Shader or Geometry Nodes)
        if is_tree_node_group:
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to new Node Group\n" +
                           "add_group_nodes('" + mat.edit_tree.name + "')\n")
        # if using World material node tree
        elif bpy.data.worlds.get(mat.id.name):
            m2p_text.write("\n# use Python script to create World material, including nodes and links\n" +
                           "world_mat = bpy.data.worlds.new(\""+mat.id.name+"\")\n" +
                           "world_mat.use_nodes = True\n" +
                           "add_shader_nodes(world_mat)\n")
        # if using Compositor node tree
        elif mat.edit_tree.bl_idname == 'CompositorNodeTree':
            m2p_text.write("\n# use Python script to add nodes, and links between nodes, to Compositor node tree\n" +
                           "add_shader_nodes(bpy.context.scene)\n")
        # if using Linestyle node tree
        elif bpy.data.linestyles.get(mat.id.name):
            m2p_text.write("\n# use Python script to create Linestyle, including nodes and links\n" +
                           "linestyle_mat = bpy.data.linestyles.new(\""+mat.id.name+"\")\n" +
                           "linestyle_mat.use_nodes = True\n" +
                           "add_shader_nodes(linestyle_mat)\n")
        # else using Object Material Shader Nodes
        else:
            m2p_text.write("\n# use Python script to create Material, including nodes and links\n" +
                           "mat = bpy.data.materials.new(\""+mat.id.name+"\")\n" +
                           "mat.use_nodes = True\n" +
                           "add_shader_nodes(mat)\n")

    # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
    m2p_text.current_line_index = 0
    m2p_text.cursor_set(0)

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
            LOC_DEC_PLACES_UNI_NODE_OPT: scn.Mat2Py.write_loc_decimal_places,
            WRITE_DEFAULTS_UNI_NODE_OPT: scn.Mat2Py.write_default_values,
            WRITE_LINKED_DEFAULTS_UNI_NODE_OPT: scn.Mat2Py.write_linked_default_values,
            WRITE_ATTR_NAME_UNI_NODE_OPT: scn.Mat2Py.write_attrib_name,
            WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT: scn.Mat2Py.write_attrib_width_and_height,
            WRITE_ATTR_SELECT_UNI_NODE_OPT: scn.Mat2Py.write_attrib_select,
        }
        create_code_text(context, scn.Mat2Py.num_space_pad, scn.Mat2Py.keep_links, scn.Mat2Py.make_function,
                         scn.Mat2Py.delete_existing, scn.Mat2Py.ng_output_min_max_def, uni_node_options)
        return {'FINISHED'}
