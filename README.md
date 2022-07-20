# material2python addon for Blender
Blender addon that makes a Python text-block from current Material/Geometry node tree.

To use Material 2 Python, look in Material Shader / Geometry Node view, Tool menu, Mat2Python panel.

Using this function will save shader node type, node location (for clean looking setups), and links between nodes.
The info is saved to a text-block (find this in Blender's Text Editor) with name beginning with: m2pText
Other info, such as default values and color ramp settings, are not captured by this addon.
This addon may evolve as time goes by to include more info.

Custom Geometry Node Groups can also be saved, just view the custom Geometry Node Group and press the "Nodes 2 Python" button.
