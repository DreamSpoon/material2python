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

import bpy as boop

M2P_TEXT_NAME = "m2pText"

class Mat2Python(boop.types.Operator):
    """Make Python text-block from current Material node tree"""
    bl_idname = "major.awesome"
    bl_label = "Material to Python"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, fun):
        s = fun.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ("CompositorNodeTree", "ShaderNodeTree", "TextureNodeTree"):
            return True
        return False

    def execute(self, fun):
        fs = fun.scene
        self.do_it(fun, fs.M2P_NumSpacePad, fs.M2P_KeepLinks, fs.M2P_MakeFunction, fs.M2P_DeleteExisting,
            fs.M2P_UseEditTree)
        return {'FINISHED'}

    @classmethod
    def do_it(cls, fun, space_pad, keep_links, make_into_function, delete_existing, use_edit_tree):
        pres = ""
        if isinstance(space_pad, int):
            pres = " " * space_pad
        elif isinstance(space_pad, str):
            pres = space_pad

        mat = fun.space_data

        m2p_text = boop.data.texts.new(M2P_TEXT_NAME)

        the_tree_to_use = mat.node_tree
        if use_edit_tree:
            the_tree_to_use = mat.edit_tree

        node_group = boop.data.node_groups.get(the_tree_to_use.name)
        is_the_tree_in_node_groups = (node_group != None)

        if make_into_function:
            if is_the_tree_in_node_groups:
                m2p_text.write("import bpy\n\n# add nodes and links to node group \n" +
                               "def add_group_nodes(node_group_name):\n")
            else:
                m2p_text.write("import bpy\n\n# add nodes and links to material\ndef add_material_nodes(material):\n")

        if is_the_tree_in_node_groups:
            m2p_text.write(pres + "# initialize variables\n")
            m2p_text.write(pres + "new_nodes = {}\n")
            m2p_text.write(pres + "new_node_group = bpy.data.node_groups.new(name=\""+the_tree_to_use.name+"\", type='"+
                           the_tree_to_use.bl_idname+"')\n")
            # get the node group inputs and outputs
            for ng_input in node_group.inputs:
                m2p_text.write(pres + "new_node_group.inputs.new(type='"+ng_input.bl_socket_idname+"', name=\"" +
                               ng_input.name+"\")\n")
            for ng_output in node_group.outputs:
                m2p_text.write(pres + "new_node_group.outputs.new(type='"+ng_output.bl_socket_idname+"', name=\"" +
                               ng_output.name+"\")\n")

            m2p_text.write(pres + "tree_nodes = new_node_group.nodes")
        else:
            m2p_text.write(pres + "# initialize variables\n")
            m2p_text.write(pres + "new_nodes = {}\n")
            m2p_text.write(pres + "tree_nodes = material.node_tree.nodes\n")

        if delete_existing:
            m2p_text.write(pres + "# delete all nodes\n")
            m2p_text.write(pres + "tree_nodes.clear()\n")
        m2p_text.write("\n" + pres + "# material shader nodes\n")

        # write info about the individual nodes
        for tree_node in the_tree_to_use.nodes:
            m2p_text.write(pres + "node = tree_nodes.new(type=\"%s\")\n" % tree_node.bl_idname)
            m2p_text.write(pres + "node.name = \"%s\"\n" % tree_node.name)
            m2p_text.write(pres + "node.label = \"%s\"\n" % tree_node.label)
            m2p_text.write(pres + "node.width = %f\n" % tree_node.width)
            m2p_text.write(pres + "node.width_hidden = %f\n" % tree_node.width_hidden)
            m2p_text.write(pres + "node.height = %f\n" % tree_node.height)
            m2p_text.write(pres + "node.color = (%f, %f, %f)\n" % tuple(tree_node.color))
            m2p_text.write(pres + "node.use_custom_color = %s\n" % tree_node.use_custom_color)
            m2p_text.write(pres + "node.location = (" + str(round(tree_node.location.x, 3)) + ", " +
                str(round(tree_node.location.y, 3)) + ")\n")
            # Node Group shader node?
            if tree_node.bl_idname == 'ShaderNodeGroup':
                # get node tree for creating Node Group shader node
                m2p_text.write(pres + "node.node_tree = bpy.data.node_groups.get(\"" + tree_node.node_tree.name + "\")\n")

            # get node inputs default value(s), each input might be [ float, (R, G, B, A), (X, Y, Z), ... ]
            # TODO: this part needs more testing re: different node input default value(s) and type(s)
            c = -1
            for node_input in tree_node.inputs:
                c = c + 1
                # ignore virtual sockets and shader sockets, no default
                if node_input.bl_idname == 'NodeSocketVirtual' or node_input.bl_idname == 'NodeSocketShader':
                    continue
                # is default value a float type?
                if isinstance(node_input.default_value, float):
                    m2p_text.write(pres + "node.inputs["+str(c)+"].default_value = "+str(node_input.default_value)+"\n")
                    continue
                # default value is an tuple/array type
                for def_val_index in range(len(node_input.default_value)):
                    m2p_text.write(pres + "node.inputs["+str(c)+"].default_value["+str(def_val_index)+"] = "+str(node_input.default_value[def_val_index])+"\n")

            m2p_text.write(pres + "new_nodes[\"" + tree_node.name + "\"] = node\n\n")

        m2p_text.write(pres + "# links between nodes\n")
        if keep_links:
            m2p_text.write(pres + "new_links = []\n")
        if is_the_tree_in_node_groups:
            m2p_text.write(pres + "tree_links = new_node_group.links\n\n")
        else:
            m2p_text.write(pres + "tree_links = material.node_tree.links\n\n")
        for tree_link in the_tree_to_use.links:
            flint = ""
            if keep_links:
                flint = "link = "
            m2p_text.write(pres + flint + "tree_links.new(new_nodes[\"" + tree_link.from_socket.node.name +
                "\"].outputs[" + str(cls.get_output_num_for_link(tree_link)) + "], new_nodes[\"" +
                tree_link.to_socket.node.name + "\"].inputs[" + str(cls.get_input_num_for_link(tree_link)) + "])\n")
            if keep_links:
                m2p_text.write(pres + "new_links.append(link)\n\n")

        if make_into_function:
            if is_the_tree_in_node_groups:
                #m2p_text.write("add_group_nodes('"+the_tree_to_use.name+"'):\n")
                m2p_text.write("# use python script to add nodes, and links between nodes, to new Node Group\n" +
                               "add_group_nodes('"+the_tree_to_use.name+"')\n")
            else:
                m2p_text.write("# use python script to add nodes, and links between nodes, to the active material of " +
                               "the active object\nobj = bpy.context.active_object\n" +
                               "if obj != None and obj.active_material != None:\n" +
                               "    add_material_nodes(obj.active_material)\n")

    @classmethod
    def get_input_num_for_link(cls, tr_link):
        for c in range(0, len(tr_link.to_socket.node.inputs)):
            if tr_link.to_socket.node.inputs[c] == tr_link.to_socket:
                return c
        return None

    @classmethod
    def get_output_num_for_link(cls, tr_link):
        for c in range(0, len(tr_link.from_socket.node.outputs)):
            if tr_link.from_socket.node.outputs[c] == tr_link.from_socket:
                return c
        return None
