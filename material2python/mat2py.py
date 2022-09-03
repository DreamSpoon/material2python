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

NODES_WITH_WRITE_OUTPUTS = ['ShaderNodeValue']

# add escape characters to backslashes and double-quote chars in given string
def esc_char_string(in_str):
    return in_str.replace('\\', '\\\\').replace('"', '\\"')

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
    is_the_tree_in_node_groups = (node_group != None)

    m2p_text.write("# Blender Python script to re-create ")
    if make_into_function:
        if is_the_tree_in_node_groups:
            m2p_text.write("Node Group named \""+the_tree_to_use.name+"\"\n\nimport bpy\n\n# add nodes and " +
                           "links to node group \ndef add_group_nodes(node_group_name):\n")
        else:
            m2p_text.write("material named \""+the_tree_to_use.name+"\"\n\nimport bpy\n\n# add nodes and links to " +
                           "material\ndef add_material_nodes(material):\n")

    if is_the_tree_in_node_groups:
        m2p_text.write(line_prefix + "# initialize variables\n")
        m2p_text.write(line_prefix + "new_nodes = {}\n")
        m2p_text.write(line_prefix + "new_node_group = bpy.data.node_groups.new(name=node_group_name, type='"+
                       the_tree_to_use.bl_idname+"')\n")
        # get the node group inputs and outputs
        for ng_input in node_group.inputs:
            m2p_text.write(line_prefix + "new_node_group.inputs.new(type='"+ng_input.bl_socket_idname+"', name=\"" +
                           ng_input.name+"\")\n")
        for ng_output in node_group.outputs:
            m2p_text.write(line_prefix + "new_node_group.outputs.new(type='"+ng_output.bl_socket_idname+"', name=\"" +
                           ng_output.name+"\")\n")

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
        for attr in uni_attr_default_list:
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

                if isinstance(gotten_attr, int):
                    m2p_text.write(line_prefix + "node."+attr+" = %d\n" % gotten_attr)
                elif isinstance(gotten_attr, float):
                    m2p_text.write(line_prefix + "node."+attr+" = %f\n" % gotten_attr)
                elif isinstance(gotten_attr, Color):
                    m2p_text.write(line_prefix + "node."+attr+" = (%f, %f, %f)\n" % (gotten_attr[0], gotten_attr[1],
                                                                              gotten_attr[2]))
                elif isinstance(gotten_attr, Vector):
                    m2p_text.write(line_prefix + "node."+attr+" = (%f, %f, %f)\n" % (gotten_attr[0], gotten_attr[1],
                                                                              gotten_attr[2]))
                elif isinstance(gotten_attr, str):
                    m2p_text.write(line_prefix + "node."+attr+" = \"%s\"\n" % gotten_attr)
                # unknown type, try to convert to string (without quotes) as final option
                else:
                    m2p_text.write(line_prefix + "node."+attr+" = %s\n" % str(gotten_attr))

        # node with parent is special, this node is offset by their parent frame's location
        parent_loc = Vector((0, 0))
        if tree_node.parent != None:
            parent_loc = tree_node.parent.location

        # do rounding of location values, if needed, and write the values
        precision = uni_node_options[LOC_DEC_PLACES_UNI_NODE_OPT]
        loc_x = tree_node.location.x+parent_loc.x
        loc_y = tree_node.location.y+parent_loc.y
        m2p_text.write(line_prefix + "node.location = (%0.*f, %0.*f)\n" % (precision, loc_x, precision, loc_y))

        # Geometry Nodes or Shader Nodes Group node
        if tree_node.bl_idname in ['GeometryNodeGroup', 'ShaderNodeGroup']:
            # get name of node tree referenced by node
            m2p_text.write(line_prefix + "node.node_tree = bpy.data.node_groups.get(\""+tree_node.node_tree.name+
                           "\")\n")
        # Image Texture or Environment Texture node: get image if available
        if tree_node.bl_idname in ['ShaderNodeTexEnvironment', 'ShaderNodeTexImage'] and \
                tree_node.image != None:
            m2p_text.write(line_prefix + "node.image = bpy.data.images.get(\"%s\")\n" % tree_node.image.name)
        # Object
        if tree_node.bl_idname in ['ShaderNodeTexCoord', 'ShaderNodeTexPointDensity']:
            if tree_node.object != None:
                m2p_text.write(line_prefix + "node.object = bpy.data.objects.get(\"%s\")\n" % tree_node.object.name)
        # Script
        if tree_node.bl_idname in ['ShaderNodeScript']:
            if tree_node.script != None:
                m2p_text.write(line_prefix + "node.script = bpy.data.texts.get(\"%s\")\n" % tree_node.script.name)
        # Input Vector Type
        if tree_node.bl_idname in ['FunctionNodeInputVector']:
            vec_str = ""
            for def_val_index in range(len(tree_node.vector)):
                if vec_str != "":
                    vec_str = vec_str+", "
                vec_str = vec_str+str(tree_node.vector[def_val_index])
            m2p_text.write(line_prefix + "node.vector = ("+vec_str+")\n")

        write_filtered_attribs(m2p_text, line_prefix, tree_node)

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
            # is default value a float/int/bool type?
            if isinstance(node_input.default_value, (float, int, bool)):
                m2p_text.write(line_prefix + "node.inputs["+str(input_count)+"].default_value = " + \
                               str(node_input.default_value)+"\n")
            # is default value a string type?
            elif isinstance(node_input.default_value, str):
                m2p_text.write(line_prefix + "node.inputs["+str(input_count)+"].default_value = \"" + \
                               esc_char_string(node_input.default_value)+"\"\n")
            # skip to next input if 'default_value' is not an array/list/tuple
            elif hasattr(node_input.default_value, '__len__'):
                # default value is an tuple/array type
                vec_str = ""
                for def_val_index in range(len(node_input.default_value)):
                    if vec_str != "":
                        vec_str = vec_str+", "
                    vec_str = vec_str+str(node_input.default_value[def_val_index])
                m2p_text.write(line_prefix + "node.inputs["+str(input_count)+"].default_value = ("+vec_str+")\n")
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
            # is default value a float/int/bool type?
            if isinstance(node_output.default_value, (float, int, bool)):
                m2p_text.write(line_prefix + "node.outputs["+str(output_count)+"].default_value = " + \
                               str(node_output.default_value)+"\n")
            # is default value a string type?
            elif isinstance(node_output.default_value, str):
                m2p_text.write(line_prefix + "node.outputs["+str(output_count)+"].default_value = \"" + \
                               esc_char_string(node_output.default_value)+"\"\n")
            # skip to next output if 'default_value' is not an array/list/tuple
            elif hasattr(node_output.default_value, '__len__'):
                # default value is an tuple/list/array type
                vec_str = ""
                for def_val_index in range(len(node_output.default_value)):
                    if vec_str != "":
                        vec_str = vec_str+", "
                    vec_str = vec_str+str(node_output.default_value[def_val_index])
                m2p_text.write(line_prefix + "node.outputs["+str(output_count)+"].default_value = ("+vec_str+")\n")

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
    if is_the_tree_in_node_groups:
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
        if is_the_tree_in_node_groups:
            m2p_text.write("\n# use python script to add nodes, and links between nodes, to new Node Group\n" +
                           "add_group_nodes('"+the_tree_to_use.name+"')\n")
        else:
            m2p_text.write("\n# use python script to add nodes, and links between nodes, to the active material " +
                           "of the active object\nobj = bpy.context.active_object\n" +
                           "if obj != None and obj.active_material != None:\n" +
                           "    add_material_nodes(obj.active_material)\n")
    # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
    # TODO: fix this, not working in Blender 3.1
    m2p_text.current_line_index = 0

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

def write_filtered_attribs(m2p_text, line_prefix, node):
    filtered_list = []
    for attr_name in dir(node):
        the_attr = getattr(node, attr_name)
        # filter out attributes that are built-ins (python/Blender), or callable functions, or
        # attributes that are ignored/handled elsewhere
        if attr_name.startswith('__') or attr_name.startswith('bl_') or callable(the_attr) or \
            attr_name in FILTER_OUT_ATTRIBS:
            continue
        filtered_list.append(attr_name)
        if isinstance(the_attr, str):
            m2p_text.write(line_prefix + "node."+attr_name+" = \"%s\"\n" % the_attr)
        elif isinstance(the_attr, bool):
            m2p_text.write(line_prefix + "node."+attr_name+" = %s\n" % the_attr)
        elif isinstance(the_attr, int):
            m2p_text.write(line_prefix + "node."+attr_name+" = %d\n" % the_attr)
        elif isinstance(the_attr, float):
            m2p_text.write(line_prefix + "node."+attr_name+" = %f\n" % the_attr)

class M2P_CreateText(bpy.types.Operator):
    """Make Python text-block from current Material/Geometry node tree"""
    bl_idname = "mat2py.awesome"
    bl_label = "Nodes 2 Python"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        s = context.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ("CompositorNodeTree", "ShaderNodeTree", "TextureNodeTree", "GeometryNodeTree"):
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
