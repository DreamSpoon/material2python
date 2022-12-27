# material2python addon for Blender
Make a Python text-block from any Blender Material/Geometry node tree, from Node Editor window.

To use this addon:
1) Open Node Editor window
2) Look in Tool menu -> Mat2Python panel
  - Tool menu is to the right side of Node Editor window

Press 'Nodes 2 Python' button to save currently displayed nodes to Python code text-block.

Open text-block in Blender's built-in Text Editor, new text-block's name starts with *m2pText*

The following node types can be saved to Python text-block:
- Shader Nodes
- Compositor Nodes
- Geometry Nodes

Custom node groups for any of the above types can also be saved.
Saving custom Node Group nodes works the same as saving any other nodes:
1) Show custom Node Group in Node Editor window (nodes inside group must be visible, not just node which shows name of group)
2) Press the 'Nodes 2 Python' button

Python code generated by this addon can be run immediately by pressing 'Run Script' button in Text Editor window.
In other words, the code can be immediately tested to verify that it correctly re-creates a custom node group, or simply the nodes currently visible in Node Editor window.
