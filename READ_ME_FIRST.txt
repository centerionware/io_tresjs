****WARNING: 
This script will modify your blend files with the default settings. Save them before running it. specifically - it will triangulate everything.


I created this exporter because of a few annoying bugs in the mainline threejs exporter.
Bugs I set out to fix with this exporter:
 readability. I tried, very hard, but just couldn't figure out how the entire exporter fit together. 
 rotations where incorrect by default (everything needed rotated around the Z axis in three to line up the same way as in blender)
 To much information was exported with armatured meshes (Every single pose animation was exported for every single armatured object even if the pose animation affected no bones on the armature)
 I'm sure there's others I can't think of

This exporter is _NOT_ meant to be a full replacement for the io_three exporter. io_three does much better in certain areas:
 Any armature with IK or any other constraints
 Supports other animation types such as morph targets

INSTALLATION:
Open the .py file, select all, copy, open blender, open the text editor, create a new text document node, paste, edit the output_dir near the top, then run.

The exporter will create a file with the same name as your blend file with the extension .blend.json , which can then be used with threejs. It will output to the directory you specify with output_dir (The unix format can be used on windows 10, mac, and unix. ex: /dir/dir will output to c:\dir\dir\ on windows)


This exporter also connects to my database frontend webpages to upload the models directly to my server. This functionality is disabled by default since it's all custom code, and you won't have authentication credentials, but should provide a nice easy launching point for anybody who wishes to impliment similar functionality. It's honestly only like 10 extra lines of code to upload to the server.

It's fairly straight forward to create a chunked exporter - that can upload chunked scene data to a server from a single file (Think minecraft chunks), but that code isn't included because.. well.. I want to keep something for myself and my game.
Good luck, I hope this exporter helps somebody.