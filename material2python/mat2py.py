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
from mathutils import Vector

M2P_TEXT_NAME = "m2pText"

class Mat2Python(boop.types.Operator):
    """Make Python text-block from current Material/Geometry node tree"""
    bl_idname = "major.awesome"
    bl_label = "Nodes 2 Python"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, fun):
        s = fun.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ("CompositorNodeTree", "ShaderNodeTree", "TextureNodeTree", "GeometryNodeTree"):
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

        m2p_text.write("# Blender Python script to re-create ")
        if make_into_function:
            if is_the_tree_in_node_groups:
                m2p_text.write("material Node Group named \""+the_tree_to_use.name+"\"\n\nimport bpy\n\n# add nodes and links to node group \n" +
                               "def add_group_nodes(node_group_name):\n")
            else:
                m2p_text.write("material named \""+the_tree_to_use.name+"\"\n\nimport bpy\n\n# add nodes and links to material\ndef add_material_nodes(material):\n")

        if is_the_tree_in_node_groups:
            m2p_text.write(pres + "# initialize variables\n")
            m2p_text.write(pres + "new_nodes = {}\n")
            m2p_text.write(pres + "new_node_group = bpy.data.node_groups.new(name=node_group_name, type='"+
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

        # set parenting order of nodes (e.g. parenting to frames) after creating all the nodes in the tree,
        # so that parent nodes are referenced only after parent nodes are created
        frame_parenting_text = ""
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
            m2p_text.write(pres + "node.mute = %s\n" % tree_node.mute)
            m2p_text.write(pres + "node.hide = %s\n" % tree_node.hide)

            # node with parent is special, this node is offset by their parent frame's location
            parent_loc = Vector((0, 0))
            if tree_node.parent != None:
                parent_loc = tree_node.parent.location
            m2p_text.write(pres + "node.location = (%.3f, %.3f)\n" % \
                (tree_node.location.x+parent_loc.x, tree_node.location.y+parent_loc.y))

            # Node Group shader node?
            if tree_node.bl_idname == 'ShaderNodeGroup':
                # get node tree for creating Node Group shader node
                m2p_text.write(pres + "node.node_tree = bpy.data.node_groups.get(\""+tree_node.node_tree.name+"\")\n")
            # check for node properties, other than those found in the node 'inputs' and 'outputs'
            # TODO node types to add/check here: ShaderNodeMapping, ShaderNodeRGBCurve, ShaderNodeValToRGB,
            #                                    ShaderNodeVectorCurve
            else:
                # Attribute Name
                if tree_node.bl_idname in ['ShaderNodeAttribute']:
                    m2p_text.write(pres + "node.attribute_name = \"%s\"\n" % tree_node.attribute_name)
                # Axis
                if tree_node.bl_idname in ['ShaderNodeTangent']:
                    m2p_text.write(pres + "node.axis = \"%s\"\n" % tree_node.axis)
                # Blend Type
                if tree_node.bl_idname in ['ShaderNodeMixRGB']:
                    m2p_text.write(pres + "node.blend_type = \"%s\"\n" % tree_node.blend_type)
                # Coloring
                if tree_node.bl_idname in ['ShaderNodeTexVoronoi']:
                    m2p_text.write(pres + "node.coloring = \"%s\"\n" % tree_node.coloring)
                # Color Space
                if tree_node.bl_idname in ['ShaderNodeTexEnvironment']:
                    m2p_text.write(pres + "node.color_space = \"%s\"\n" % tree_node.color_space)
                # Component
                if tree_node.bl_idname in ['ShaderNodeBsdfHair', 'ShaderNodeBsdfToon']:
                    m2p_text.write(pres + "node.component = \"%s\"\n" % tree_node.component)
                # Convert From
                if tree_node.bl_idname in ['ShaderNodeVectorTransform']:
                    m2p_text.write(pres + "node.convert_from = \"%s\"\n" % tree_node.convert_from)
                # Convert To
                if tree_node.bl_idname in ['ShaderNodeVectorTransform']:
                    m2p_text.write(pres + "node.convert_to = \"%s\"\n" % tree_node.convert_to)
                # Direction Type
                if tree_node.bl_idname in ['ShaderNodeTangent']:
                    m2p_text.write(pres + "node.direction_type = \"%s\"\n" % tree_node.direction_type)
                # Distribution
                if tree_node.bl_idname in ['ShaderNodeBsdfAnisotropic', 'ShaderNodeBsdfGlass', 'ShaderNodeBsdfGlossy',
                                           'ShaderNodeBsdfPrincipled', 'ShaderNodeBsdfRefraction']:
                    m2p_text.write(pres + "node.distribution = \"%s\"\n" % tree_node.distribution)
                # Extension
                if tree_node.bl_idname in ['ShaderNodeTexImage']:
                    m2p_text.write(pres + "node.extension = \"%s\"\n" % tree_node.extension)
                # Falloff
                if tree_node.bl_idname in ['ShaderNodeSubsurfaceScattering']:
                    m2p_text.write(pres + "node.falloff = \"%s\"\n" % tree_node.falloff)
                # Frequency
                if tree_node.bl_idname in ['ShaderNodeTexBrick']:
                    m2p_text.write(pres + "node.offset_frequency = %f\n" % tree_node.offset_frequency)
                # From Duplicate
                if tree_node.bl_idname in ['ShaderNodeTexCoord', 'ShaderNodeUVMap']:
                    m2p_text.write(pres + "node.from_dupli = %s\n" % tree_node.from_dupli)
                # Gradient Type
                if tree_node.bl_idname in ['ShaderNodeTexGradient']:
                    m2p_text.write(pres + "node.gradient_type = \"%s\"\n" % tree_node.gradient_type)
                # Ground Albedo
                if tree_node.bl_idname in ['ShaderNodeTexSky']:
                    m2p_text.write(pres + "node.ground_albedo = %f\n" % tree_node.ground_albedo)
                # Image Texture or Environment Texture node: get image if available
                if tree_node.bl_idname in ['ShaderNodeTexImage', 'ShaderNodeTexEnvironment'] and \
                        tree_node.image != None:
                    m2p_text.write(pres + "node.image = bpy.data.images.get(\"%s\")\n" % tree_node.image.name)
                # Interpolation
                if tree_node.bl_idname in ['ShaderNodeTexEnvironment', 'ShaderNodeTexPointDensity']:
                    m2p_text.write(pres + "node.interpolation = \"%s\"\n" % tree_node.interpolation)
                # Invert
                if tree_node.bl_idname in ['ShaderNodeBump']:
                    m2p_text.write(pres + "node.invert = %s\n" % tree_node.invert)
                # Musgrave Type
                if tree_node.bl_idname in ['ShaderNodeTexMusgrave']:
                    m2p_text.write(pres + "node.musgrave_type = \"%s\"\n" % tree_node.musgrave_type)
                # Mode
                if tree_node.bl_idname in ['ShaderNodeScript']:
                    m2p_text.write(pres + "node.mode = \"%s\"\n" % tree_node.mode)
                # Object
                if tree_node.bl_idname in ['ShaderNodeTexCoord', 'ShaderNodeTexPointDensity']:
                    if tree_node.object != None:
                        m2p_text.write(pres + "node.object = bpy.data.objects.get(\"%s\")\n" % tree_node.object.name)
                # Offset
                if tree_node.bl_idname in ['ShaderNodeTexBrick']:
                    m2p_text.write(pres + "node.offset = %f\n" % tree_node.offset)
                # Operation
                if tree_node.bl_idname in ['ShaderNodeMath', 'ShaderNodeVectorMath']:
                    m2p_text.write(pres + "node.operation = \"%s\"\n" % tree_node.operation)
                # Particle Color Source
                if tree_node.bl_idname in ['ShaderNodeTexPointDensity']:
                    m2p_text.write(pres + "node.particle_color_source = \"%s\"\n" % tree_node.particle_color_source)
                # Point Source
                if tree_node.bl_idname in ['ShaderNodeTexPointDensity']:
                    m2p_text.write(pres + "node.point_source = \"%s\"\n" % tree_node.point_source)
                # Projection
                if tree_node.bl_idname in ['ShaderNodeTexEnvironment']:
                    m2p_text.write(pres + "node.projection = \"%s\"\n" % tree_node.projection)
                # Radius
                if tree_node.bl_idname in ['ShaderNodeTexPointDensity']:
                    m2p_text.write(pres + "node.radius = %f\n" % tree_node.radius)
                # Resolution
                if tree_node.bl_idname in ['ShaderNodeTexPointDensity']:
                    m2p_text.write(pres + "node.resolution = %f\n" % tree_node.resolution)
                # Script
                if tree_node.bl_idname in ['ShaderNodeScript']:
                    if tree_node.script != None:
                        m2p_text.write(pres + "node.script = bpy.data.texts.get(\"%s\")\n" % tree_node.script.name)
                # Sky Type
                if tree_node.bl_idname in ['ShaderNodeTexSky']:
                    m2p_text.write(pres + "node.sky_type = \"%s\"\n" % tree_node.sky_type)
                # Space
                if tree_node.bl_idname in ['ShaderNodeTexPointDensity', 'ShaderNodeNormalMap']:
                    m2p_text.write(pres + "node.space = \"%s\"\n" % tree_node.space)
                # Squash
                if tree_node.bl_idname in ['ShaderNodeTexBrick']:
                    m2p_text.write(pres + "node.squash = %f\n" % tree_node.squash)
                # Squash Frequency
                if tree_node.bl_idname in ['ShaderNodeTexBrick']:
                    m2p_text.write(pres + "node.squash_frequency = %f\n" % tree_node.squash_frequency)
                # Turbidity
                if tree_node.bl_idname in ['ShaderNodeTexSky']:
                    m2p_text.write(pres + "node.turbidity = %f\n" % tree_node.turbidity)
                # Turbulence Depth
                if tree_node.bl_idname in ['ShaderNodeTexMagic']:
                    m2p_text.write(pres + "node.turbulence_depth = %f\n" % tree_node.turbulence_depth)
                # Use Clamp
                if tree_node.bl_idname in ['ShaderNodeMath', 'ShaderNodeMixRGB']:
                    m2p_text.write(pres + "node.use_clamp = %s\n" % tree_node.use_clamp)
                # Use Pixel Size
                if tree_node.bl_idname in ['ShaderNodeWireframe']:
                    m2p_text.write(pres + "node.use_pixel_size = %s\n" % tree_node.use_pixel_size)
                # UV Map
                if tree_node.bl_idname in ['ShaderNodeNormalMap', 'ShaderNodeTangent', 'ShaderNodeUVMap']:
                    m2p_text.write(pres + "node.uv_map = \"%s\"\n" % tree_node.uv_map)
                # Vector Type
                if tree_node.bl_idname in ['ShaderNodeVectorTransform']:
                    m2p_text.write(pres + "node.vector_type = \"%s\"\n" % tree_node.vector_type)
                # Wave Profile
                if tree_node.bl_idname in ['ShaderNodeTexWave']:
                    m2p_text.write(pres + "node.wave_profile = \"%s\"\n" % tree_node.wave_profile)
                # Wave Type
                if tree_node.bl_idname in ['ShaderNodeTexWave']:
                    m2p_text.write(pres + "node.wave_type = \"%s\"\n" % tree_node.wave_type)

            # get node input(s) default value(s), each input might be [ float, (R, G, B, A), (X, Y, Z), shader ]
            # TODO: this part needs more testing re: different node input default value(s) and type(s)
            input_count = -1
            for node_input in tree_node.inputs:
                input_count = input_count + 1
                # ignore virtual sockets and shader sockets, no default
                if node_input.bl_idname == 'NodeSocketVirtual' or node_input.bl_idname == 'NodeSocketShader':
                    continue
                # if node doesn't have attribute 'default_value', then cannot save the value - so continue
                if not hasattr(node_input, 'default_value'):
                    continue
                # is default value a float type?
                if isinstance(node_input.default_value, float):
                    m2p_text.write(pres + "node.inputs["+str(input_count)+"].default_value = " + \
                                   str(node_input.default_value)+"\n")
                    continue
                # skip to next input if 'default_value' is not a list/tuple
                if not isinstance(node_input.default_value, (list, tuple)):
                    continue
                # default value is an tuple/array type
                for def_val_index in range(len(node_input.default_value)):
                    m2p_text.write(pres + "node.inputs["+str(input_count)+"].default_value["+str(def_val_index) + \
                                   "] = "+str(node_input.default_value[def_val_index])+"\n")
            # get node output(s) default value(s), each output might be [ float, (R, G, B, A), (X, Y, Z), shader ]
            # TODO: this part needs more testing re: different node output default value(s) and type(s)
            output_count = -1
            for node_output in tree_node.outputs:
                output_count = output_count + 1
                # ignore virtual sockets and shader sockets, no default
                if node_output.bl_idname == 'NodeSocketVirtual' or node_output.bl_idname == 'NodeSocketShader':
                    continue
                # if node doesn't have attribute 'default_value', then cannot save the value - so continue
                if not hasattr(node_output, 'default_value'):
                    continue
                # is default value a float type?
                if isinstance(node_output.default_value, float):
                    m2p_text.write(pres + "node.outputs["+str(output_count)+"].default_value = " + \
                                   str(node_output.default_value)+"\n")
                    continue
                # skip to next input if 'default_value' is not a list/tuple
                if not isinstance(node_output.default_value, (list, tuple)):
                    continue
                # default value is an tuple/array type
                for def_val_index in range(len(node_output.default_value)):
                    m2p_text.write(pres + "node.outputs["+str(output_count)+"].default_value["+str(def_val_index) + \
                                   "] = "+str(node_output.default_value[def_val_index])+"\n")

            m2p_text.write(pres + "new_nodes[\"" + tree_node.name + "\"] = node\n\n")
            # save a reference to parent node for later, if parent node exists
            if tree_node.parent != None:
                frame_parenting_text = frame_parenting_text + pres + "new_nodes[\"" + tree_node.name + \
                    "\"].parent = new_nodes[\"" + tree_node.parent.name + "\"]\n"

        # do node parenting if needed
        if frame_parenting_text != "":
            m2p_text.write(pres + "# parenting of nodes\n" + frame_parenting_text + "\n")

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
                m2p_text.write("# use python script to add nodes, and links between nodes, to the active material of "+
                               "the active object\nobj = bpy.context.active_object\n" +
                               "if obj != None and obj.active_material != None:\n" +
                               "    add_material_nodes(obj.active_material)\n")
        # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
        m2p_text.current_line_index = 0

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
