import bpy
#import os
import json
import uuid
import base64
import copy
import mathutils
import os.path
import re
import gpu


output_dir = "/xampp/htdocs/content/"
global_output_filename = bpy.path.basename(bpy.context.blend_data.filepath)

scene = bpy.context.scene
active_mesh = None

#/* Set the scene context to avoid that stupid can't apply in edit mode error */
bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

# server_file_upload is immediatly after writing a file to the hdd if true
do_server_file_upload = False

float_precision = 6
apply_subsurf = False
apply_triangulate = True
Apply_Mesh_Transforms = False # not really needed - as long as you select everything in the scene and apply location + rotation, then control+alt+shift+c and set origin to geometry.
use_shader_materials = False # Don't use this unless you absolutely know what you're doing...



do_cache = True # Will reduce HDD writes by not re-writing if the output file is the same as the existing json file - if it exists
do_only_first = False
ids = [[0]] #This isn't necessary for the non-chunked exporter
area = 0

float_translate_string = '%.' + str(float_precision) + 'f'






def deselect_all_mesh():
    for i in bpy.context.selected_objects:
        i.select = False



def has_children(i):
    try:
        c = i.children
        return True
    except AttributeError:
        return False
    
def is_iterable(i):
    try:
        some_object_iterator = iter(i)
        return True
    except TypeError as te:
        pass
    try:
        for c in i:
            break
        return True
    except:
        return False;
    
def iter(i, f, o):
    f(i,o)
    if (has_children(i)):
        for c in i.children:
            if(has_children(c) or is_iterable(c)):
                iter(c,f,o)
            else:
                f(c,o)
    if (is_iterable(i)):
        for c in i:

            if(has_children(c) or is_iterable(c)):
                iter(c,f,o)        
            else:
                f(c,o)    

def dump(obj):
    for attr in dir(obj):
        if hasattr( obj, attr ):
            print( "obj.%s = %s" % (attr, getattr(obj, attr)))
    #for val in obj.keys():
    #    print( "obj.%s = %s" % (val, obj[val]))




def chunked_exporter(chunk_id, export_objs, chunk_offset):
    output_filename = global_output_filename + str(chunk_id) + ".json"
    prop_server_id_number = chunk_id

    def server_file_upload(output_string, prop_server_id_number):
        #from requests import session
        import requests
        import msgpack
        cred_json = None
        with open('/not_so_secure/exporter_creds.json','r') as f:
            cred_json = f.read()
        import json
        creds = json.loads(cred_json)
        
        headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'
        }
        payload = { 'Username': creds['username'], 'Password': creds['password'] }
        file_payload = {
            'id': prop_server_id_number,
#            'file_msgpack': msgpack.packb(json.loads(output_string)),
            'file_json': output_string,
            'filename':output_filename
        }
        #print(len(file_payload['file_msgpack']))
        c = requests.session()
        c.get("https://www.centerionware.com") # Ahah.
        l_response = c.post('https://www.centerionware.com/content.business', data=payload, headers=headers)
        #print(l_response.headers)
        #print(l_response.text)
     
        
        response = c.post('https://www.centerionware.com/content.business/Game-One/dbo/Edit%20chunk_resources_prop_resource.mux', data=file_payload,headers=headers)
        #print(response.headers)
        print(response.text)






    def str_dump(obj):
        s = ""
        for val in obj.keys():
            s = s + ( "obj.%s = %s\n" % (val, obj[val]))
        return s

    output_json = {
        'metadata': {"generator":"io_tresjs", "sourceFile": bpy.path.basename(bpy.context.blend_data.filepath), "version":0.1, "type":"Object" },
        'materials': [],
        'images': [],
        'object': [],
        'geometries': [],
        'animations': [],
        'textures' : []
    }
    buffered_stuff = {
        'metadata': {"generator":"io_tresjs", "sourceFile": bpy.path.basename(bpy.context.blend_data.filepath), "version":0.1, "type":"Object" },
        'materials': [],
        'images': [],
        'object': [],
        'geometries': [],
        'animations': [],
        'textures' : []
    }
    scene_json = {
     "type":"Scene",
     "matrix":[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],
     "uuid": str(uuid.uuid4()),
     "children":[]
    }

    #os.system('cls')


    from math import radians
    import mathutils
    from mathutils import Euler, Matrix

    def parse_matrix(matrix_i):
       # print(matrix_i)
        matrix = matrix_i.copy()

        # Apply a 180 around Z...
        
        # https://blender.stackexchange.com/questions/44760/rotate-objects-around-their-origin-along-a-global-axis-scripted-without-bpy-op
        euler = Euler(map(radians, (0, 90, 0)), 'XZY')
        ob = bpy.context.object
        loc, rot, scale = matrix_i.decompose()
        smat = Matrix()
        for i in range(3):
            smat[i][i] = scale[i]
        #matrix = Matrix.Translation(loc) * euler.to_matrix().to_4x4() * smat
        
        rot = rot.inverted()
        rot.z = -rot.z;
        
        #print( "Scale ... ")
        #print(scale)
        # the scale should really be put back in here, but since rotation and scale should be applied on everything anyway, it doesn't hurt to leave it out. It would be nice to be able to not have to apply scale.
        #scl = Matrix.Scale(0, 4, (1,1,1))
        scl_x = Matrix.Scale(scale.x, 4, (1,0,0))
        scl_y = Matrix.Scale(scale.y, 4, (0,1,0))
        scl_z = Matrix.Scale(scale.z, 4, (0,0,1))
        scl = scl_x * scl_y * scl_z # This can't be right. 
        
        
        
        rm = Matrix().to_3x3()
        rm.rotate(rot)
        rm = rm.to_4x4()
        tm = Matrix.Translation(loc)
      #  inv_scale = scl.copy()
       # inv_scale.invert()
        matrix = (rot.to_matrix().to_4x4() * euler.to_matrix().to_4x4() )
    #    nm = rm
    #    nm = Matrix()
    #    nm.Translation(loc)
        #nm.rotate(rot)
    #    nm.Scale(scale)
        #matrix = nm
        #/* invert the rotation */
        
        
        arr = [
            matrix[0][0],matrix[1][0],matrix[2][0], matrix[3][0],
            matrix[0][1],matrix[1][1],matrix[2][1], matrix[3][1],
            matrix[0][2],matrix[1][2],matrix[2][2], matrix[3][2],
            #scale.x,matrix[1][0],matrix[2][0], matrix[3][0],
            #scale.y,matrix[1][1],matrix[2][1], matrix[3][1],
            #scale.z,matrix[1][2],matrix[2][2], matrix[3][2],
            
            (loc.y-chunk_offset['z']),loc.z,(loc.x-chunk_offset['x']),matrix[3][3]
        ]

        for v in range(0, len(arr)):
            arr[v] = float( (float_translate_string % (arr[v]) ) ) 
        return arr

    def color_string(r, g, b):
        d = "0x%0.2X%0.2X%0.2X" % (int(r), int(g), int(b))
        return int(d, 0)

    def color_helper(color):
        return color_string(color.r*255,color.g*255,color.b*255)
        

    def parse_one_light(light,type):
        output_obj = {
            "name":light.name,
            "uuid":str(uuid.uuid4()),
            "matrix": parse_matrix(light.matrix_world),
            "visibile":light.is_visible(scene), # Need to start polling is_visible...
            "type":type,
            "color":color_helper(light.data.color),
            "distance":light.data.distance,
            "intensity":light.data.energy,
            "decayExponent":2,
            "userData":{}
        }
        scene_json['children'].append(output_obj)
        return

    def parse_light(light):
        if(light.data.type == "SPOT"):
            parse_one_light(light, "SpotLight")
        else:
            parse_one_light(light, "PointLight")
        return
    import numbers
    def parse_custom_props(object, proplist):
        for val in object.keys():
            if(val != '_RNA_UI' and val != 'cycles' and val != 'cycles_visibility'):
                if(isinstance(object[val], str) or isinstance(object[val], numbers.Number)):
                    #print(object[val])
                    #if(isinstance(object[val],str)):
                    #    proplist[val] = object[val].replace("\"","\\\"")
                    #else:
                    proplist[val] = object[val]
                else:
                    #for v in object[val]:
                        #print("K:V, :%s" %(v)) 
                    proplist[val] = json.dumps(object[val].to_list())


    def parse_texture(tex):
        # Packs the image into the blend file.. so they can all be easily accessed the same way.
        # Should make sharing threejs-ified things easier to share too
        #try:
            #dump(tex)
        #except:
            #pass
        
        if(tex.texture.image.packed_file == None):
            tex.texture.image.pack()
        out_texture = {
            'name':tex.texture.image.filepath,
            'url':"data:image/"+tex.texture.image.file_format.lower()+";base64,"+base64.encodestring(tex.texture.image.packed_file.data).decode('utf-8').replace('\n',''),
            'uuid': str(uuid.uuid4())
        }
        return out_texture #It just appends this to the output_json.textures.. hmm.


    def parse_animations(mesh, bone_names, geom_json):
        #Go through all the animations, find the ones with bones using names of the bones on the mesh
        #Add them to a heirarchy thingamagic and keyframe and such.
        animation_json = { # A basic animation
            "fps":24,
            "name":"",
            "hierarchy":[],
            "length":0
        }
        animation_frame = { # These are basically bone holders
            "parent":-1,
            "keys":[]
        }
        an_animation_frame_key = { # The keyframe info for the bones
            "pos":[],
            "scl":[],
            "rot":[],
            "time":0
        }
        
        # Number the bones
        bone_numbers = {}
        num = -1;
        for b in bone_names:
            bone_numbers[b] = num
            num += 1
        
        def find_frame_key_time(bone_frame, time, bone_number):
     #       print(bone_frame)
     #       dump(bone_frame)
            for i in bone_frame['keys']:
                if i['time'] == time:
                    return i
            return None
        def find_animation(animations, anim):
            for a in animations:
                if(a['name'] == anim):
                    return a
            return None
        
        def find_animation_frame(animations,bone_number, anim_name):
            for a in animations:
                if(a['name'] == anim_name):
                    for b in a['hierarchy']:
                        if(b['parent'] == bone_number):
                            return b
            return None
        
        def create_animation(animations, anim_name):
            al = find_animation(animations, anim_name)
            if(al != None): return al
            new_anim = copy.deepcopy(animation_json)
            new_anim['name'] = anim_name
            animations.append(new_anim)
            return new_anim
        def create_bone_frame(animations, bone_number, anim):
    #        print(anim)
            al = find_animation_frame(animations, bone_number, anim['name'])
            if(al != None): return al
            new_bf = copy.deepcopy(animation_frame)
            new_bf['parent'] = bone_number
            anim['hierarchy'].append(new_bf)
            return new_bf
            
        def c_inner(animations,anim_name,bone_number,time,anim,bone_frame):
            frame = find_frame_key_time(bone_frame, time, bone_number)
            if(frame != None): return frame
            new_kf = copy.deepcopy(an_animation_frame_key) #dict(an_animation_frame_key.copy())
            #print("new_kf")
            #print(new_kf)
            #print("...................xxxxxxxxx.........")
            new_kf['time'] = time
            bone_frame['keys'].append(new_kf)
            return new_kf
        def create_animation_frame(animations, anim_name, bone_number,time):
            anim = create_animation(animations, anim_name)
            bone_frame = create_bone_frame(animations, bone_number, anim)
            c_inner(animations,anim_name,bone_number,time,anim,bone_frame)
        exp_animations = []
        
        # Looks like a seperate fcurve for each part of the animation
        # eg: bone_x_location_x , then keyframes per fcurve

        animations = bpy.data.actions
        for action in animations:
            for curve in action.fcurves:
                for b in bone_names:
                    if curve.group.name == b:
                            # Get the animation
                            anim = create_animation(exp_animations, action.name)
                            # get the bone frame
                            bone_frame = create_bone_frame(exp_animations, bone_numbers[b], anim)
                            for k in curve.keyframe_points:
                                time = k.co.x/anim['fps']
                                anim_frame = c_inner(exp_animations, action.name, bone_numbers[b], time, anim,bone_frame)
                                if(anim['length'] < time): anim['length'] = time
                                #print('.x.x..x.x.x')
                                #print(anim_frame)
                                #print('.x.x..x.x.x')
                                if( curve.data_path.endswith('.location') ):
                                    anim_frame['pos'].append(k.co.y)
                                if( curve.data_path.endswith('.scale') ):
                                    anim_frame['scl'].append(k.co.y)
                                if( curve.data_path.endswith('.rotation_quaternion') ):
                                    anim_frame['rot'].append(k.co.y)
                #key_frame = create_animation_frame(exp_animations, action.name, bone_numbers[b], time)
                        #Switch fcurve type.. keep track of xyz in a counter
                        #Add this action to the animations for this mesh..
        # The rotations are all in wxyz, need to be swapped to xyzw
        def swap_four(array, position, parent):
            #What if the bone itself is rotated though, say, 90 along the X. Does the fcurve solve this for us or do we have to solve that?
            # consindering I'm seeing the spinner rotate around it's global y axis instead of the bones rotated by 90 along the x axis, I think it should be solved here.
            # Apply the bones rotation to to this rotation in the array.
            # Parent no longer means owner of this array, it means which bone is owner of the position in the array ...???
            if(len(array) < position+4): return
            w = array[position]
            x = array[position+1]
            y = array[position+2]
            z = array[position+3]
            
            i = mathutils.Quaternion((w,x,y,z))
            #i = get_armature(mesh).data.bones[parent+1].matrix.to_quaternion() * i # Doesn't freaking help. arg!
            #i = mathutils.Quaternion([w,x,y,z])
            #q.invert()
            #i = q
            
            array[position] = i.x
            array[position+1] = i.z
            array[position+2] = i.y
            array[position+3] = i.w
            return
        def swap_three(array, position):
            if(len(array) < position+3): return
            x = array[position]
            y = array[position+1]
            z = array[position+2]
            array[position] = -x
            array[position+1] = y
            array[position+2] = -z
            return
        def neg_pos(array, pos):
            array[pos] = -array[pos]
            
        #print("......")
        #print(an_animation_frame_key)          
        #print("......")
        for i in exp_animations:
            for j in i['hierarchy']:
                for k in j['keys']:
                    swap_four(k['rot'], 0, j['parent'])
                    swap_three(k['pos'],0)
                    if(len(k['rot']) == 0):
                        k.pop('rot',None)
                    if(len(k['pos']) == 0):
                        k.pop('pos',None)
                    if(len(k['scl']) == 0):
                        k.pop('scl',None)
        # Done swapping rotations
        #geom_json['animations'] = exp_animations

        return exp_animations



    def get_armature(mesh):
        for i in mesh.modifiers:
            if(i.type == 'ARMATURE'):
                return i.object
        return None


        
    def append_list(item, list):
        if(not is_iterable(item)):
            list.append(item)

    def parse_bone_names(bone, list):
        try:
            t = bone.head
        except:
            return
        list.append(bone.name)
        
    def get_vertex_group(mesh, name):
        for i in mesh.vertex_groups :
            if( i.name == name ):
                return i


    
    # float( float_translate_string % (value) )
    def parse_uvs(layers):
        out = []
        for layer in layers:
            cl = []
            for dp in layer.data:
                cl.append(float( float_translate_string % (dp.uv[0]) ))
                cl.append(float( float_translate_string % (dp.uv[1]) ))
            out.append(cl)
        return out

    def parse_geometry(mesh):
        
        armature = get_armature(mesh)
        
        def parse_bone(bone, list):
            try:
                t = bone.head
            except:
                return
            bone_position = bone.matrix_local.to_translation() #bone.matrix_local.(bone.head.xyz-bone.tail.xyz)
            #print("processing bone.")
            bone_position = bone_position - mesh.location
            #print(bone.name)
            #print(bone_position)
            quat = bone.matrix.to_quaternion()
            b_json = {
                "name":bone.name,
                "pos": [0,0,0], #[-bone_position.x,bone_position.z,-bone_position.y],
                "rotq": [0,0,0,1],#[quat.x,quat.y,quat.z,quat.w],
                "parent":-1
            }
            list.append(b_json)
        
        for i in output_json['geometries']:
            if( i['name']  == mesh.data.name):
                return i['uuid']

        #print("Parsing mesh " + mesh.name)
        buffered_stuff['geometries'].append(mesh)

        bones = []
        
        out_geom = { 
            "name":mesh.data.name,
            "type":"Geometry", 
            "uuid":str(uuid.uuid4()),
            'userData': {}, 
            "data": { 
                "vertices":[], 
                "animations":[], 
                "normals":[], 
                "bones":[], 
                "skinWeights":[], 
                "skinIndices":[], 
                "faces":[], 
                "influencesPerVertex":3,
                "uvs":[[]] 
                }
        }
        parse_custom_props(mesh.data, out_geom['userData'])

        #bpy.context.scene.objects.active = mesh;
        #bpy.ops.object.modifier_apply(modifier="triangulate")
        bone_names = []
        
        if(armature != None):
            iter(armature.data.bones, parse_bone, out_geom['data']['bones'])
            iter(armature.data.bones, append_list, bones)
            iter(armature.data.bones, parse_bone_names, bone_names)
        out_geom['data']['influencesPerVertex'] = len(bone_names)
        
        bpy.context.scene.objects.active = mesh
        
        #boo = mesh.modifiers.new('ESSSSS', 'EDGE_SPLIT')
        #bpy.ops.object.modifier_apply(apply_as='DATA', modifier="ESSSSS") 
        if "whole_ground" in mesh.name and apply_subsurf == True:
            boo = mesh.modifiers.new('SUB', 'SUBSURF')
            boo.subdivision_type = 'SIMPLE'
            boo.levels = 1
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="SUB") 
        if(apply_triangulate == True):
            boo = mesh.modifiers.new('TRI', 'TRIANGULATE')
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="TRI") 

        out_geom['data']['uvs'] = parse_uvs(mesh.data.uv_layers)
        out_geom['data']['animations'] = parse_animations(mesh, bone_names, out_geom)
        
        for i in mesh.data.vertices:
            fd = i.co # mesh.matrix_world * i.co
            fn = i.normal # mesh.matrix_world * i.normal
            #transl = matrix.translation

            out_geom['data']['vertices'].append(float(float_translate_string % (-fd.x)))
            out_geom['data']['vertices'].append(float(float_translate_string % (fd.z)))
            out_geom['data']['vertices'].append(float(float_translate_string % (fd.y)))
            #out_geom['data']['vertices'].append(fd.x)
            #out_geom['data']['vertices'].append(fd.z)
            #out_geom['data']['vertices'].append(fd.y)
            #Vertex Normals
            out_geom['data']['normals'].append(float(float_translate_string % (fd.x)))
            out_geom['data']['normals'].append(float(float_translate_string % (fd.y)))
            out_geom['data']['normals'].append(float(float_translate_string % (fd.z)))
            
            #out_geom['data']['normals'].append(fn.x)
            #out_geom['data']['normals'].append(fn.y)
            #out_geom['data']['normals'].append(fn.z)
            
            if(len(bone_names) != 0):
                for j in range(0, len(bone_names)):
                    try:
                        for k in mesh.vertex_groups:
                            #dump(j)
                            #dump(bones[j])
                            if(k.name == bones[j].name):
                                weight = k.weight(i.index)
                                out_geom['data']['skinWeights'].append(weight)
                                out_geom['data']['skinIndices'].append(j)
                    except RuntimeError:
                        out_geom['data']['skinWeights'].append(0)
                        out_geom['data']['skinIndices'].append(j)
        uv_index = 0
        for i in mesh.data.polygons:
            out_geom['data']['faces'].append(int('00001000',2)) # This is where the options are stored.
    #   Available Options: 
    #                   isQuad = isBitSet( type, 0 );
    #                   hasMaterial = isBitSet( type, 1 );
    #                   hasFaceVertexUv = isBitSet( type, 3 );
    #                   hasFaceNormal = isBitSet( type, 4 );
    #                   hasFaceVertexNormal = isBitSet( type, 5 );
    #                   hasFaceColor = isBitSet( type, 6 );
    #                   hasFaceVertexColor = isBitSet( type, 7 );
            
            for j in i.vertices:
                out_geom['data']['faces'].append(j)
            if(len(out_geom['data']['uvs']) > 0):
                for j in i.vertices:
                    out_geom['data']['faces'].append(uv_index)
                    uv_index += 1

            #Face Normals
        if(0): #Use vertex normals.
            out_geom['data']['normals'].append(i.normal.x)
            out_geom['data']['normals'].append(i.normal.y)
            out_geom['data']['normals'].append(i.normal.z)

        output_json['geometries'].append(out_geom)

        return out_geom['uuid']

    def parse_mesh(mesh):
        active_mesh = mesh


        def parse_material(material, materials):
            skin = False
            try:
                #print(active_mesh.parent.type)
                if active_mesh.parent.type == 'ARMATURE':
                    skin = True
            except:
                pass
            
            try:
                t = material.specular_color
            except:
                return
            def get_texture_uuid(i):
                if (i not in buffered_stuff['textures']):
                    return None
                else:
                    for j in output_json['images']:
                        if(j['name'] == i.texture.image.filepath):
                            return j['uuid']
            
            def get_image(i):
                return get_texture_uuid(i)
            # Textures first
            my_textures = []
            for i in material.texture_slots:
                if( i != None ):
                    p = True
                    try:
                        t = i.texture.image
                    except:
                        p = False
                    if not p: continue
                    id = get_texture_uuid(i)
                    if (id == None):
                        t = parse_texture(i)
                        my_textures.append(t['uuid'])
                        output_json['images'].append(t)
                        buffered_stuff['textures'].append(i)
                    else:
                        my_textures.append(id)

            if material in buffered_stuff['materials']:
                for i in output_json['materials']:
                    if(i['name'] == material.name):
                        if(skin and i['skinning'] == False):
                            continue;
                        materials.append(i['uuid'])
                        return i['uuid']

            buffered_stuff['materials'].append(material)
            output_materials = {}
            if use_shader_materials == True:
                output_material = {
                    "uuid":str(uuid.uuid4()),
                    'name': material.name,
                    "type":"RawShaderMaterial",
                    "depthFunc":3,
                    "depthTest":True,
                    "depthWrite":True,
                    "wireframe":True,
                    "skinning":skin,
                    "morphTargets":False,
                    "uniforms": {},
                    "vertexShader":"",
                    "fragmentShader":"",
                    'userData': {}
                }
                shader_details = gpu.export_shader(bpy.context.scene,material)
                
                
                #need_replaced = [/gl_Vertex/, /gl_Normal/, /gl_Color/, /gl_SecondaryColor/, /gl_MultiTexCoord[0-7]/, /gl_fogCoord/]
                
                replacements = [
                    ['position', 'blender_position'],
                    [r'gl_Vertex', 'position'], 
                    ['normal', 'blender_normal'],
                    ['gl_Position', 'position'],
                    ['blender_normalize', 'normalize'],
                    ['uv', 'blender_uv'],
                    
                    [r'gl_Normal', 'normal'], 
                    #['vec3 blender_normal = normal', ''],
                    ['vec4 blender_position = position;', 'vec4 blender_position = vec4(position.xyz, 1);'],
                    ['gl_ProjectionMatrix', 'projectionMatrix'],
                    ['gl_ModelViewMatrix','modelViewMatrix'],
                    [r'\n[\s]*?gl_ClipVertex.*?\n', ''],
                    
                    #[r'\n([\s]*?)in ', '\nvarying '],
                    #[r'\n([\s]*?)out ', '\nvarying '],
                    [r'\n[ \t\n\r]+\n','\n'],
                    ['attblender_','att_'],
                    
                    ['\(1 \- strength', '(1.0 - strength'],
                    ['\+ 1\)', '+ 1.0)'],
                    ['modelViewMatrixInverse','inverse(modelViewMatrix)'],
                    [r'texture(?![0-9D \t\n]+\(||Cube[ \t\n]+\()', 'renamed_texture'],
                    [r'texture(Cube||[0-9D \t\n]+)\(', 'texture(']
                    #['texturecurvemap','curvemap']
                    # the word texture is now reserved, variables named it need to be renamed
                    # functions like texture2D need to be renamed to texture(...)
                    # 
                    
                ] 
                #vec4 position = position;', 'vec4 position = vec4(position,1);]]
               
                
                
                output_material['fragmentShader'] = shader_details['fragment'].replace("\r","\n")
                output_material['vertexShader'] = shader_details['vertex'].replace("\r","\n")
                import re
                the_re = re.compile(r'\(([^)]+)\)')
                
                #output_material['fragmentShader'] = re.sub(r'\n([\s]*?)in ','\nvarying ', output_material['fragmentShader']).encode('ascii').decode('ascii')
                #output_material['vertexShader'] = re.sub(r'\n([\s]*?)out ', '\nvarying ', output_material['vertexShader']).encode('ascii').decode('ascii')
                output_material['fragmentShader'] = re.sub(r'\n([\s]*?)varying ', '\nout ', output_material['fragmentShader']).encode('ascii').decode('ascii')
                output_material['vertexShader'] = re.sub(r'\n([\s]*?)varying ', '\nout ', output_material['vertexShader']).encode('ascii').decode('ascii')                
                
                for a in replacements:
                    print(a)
                    output_material['fragmentShader'] = re.sub(a[0], a[1], output_material['fragmentShader'])
                    output_material['vertexShader'] = re.sub(a[0], a[1], output_material['vertexShader'])
                    
                    
                matches = the_re.findall(output_material['fragmentShader'])
                for match in matches:
                    output_material['fragmentShader']  = output_material['fragmentShader'].replace(match, match.replace("varying ", "out "))
                matches = the_re.findall(output_material['vertexShader'])
                for match in matches:
                    output_material['vertexShader']  = output_material['vertexShader'].replace(match, match.replace("varying ", "out "))

                inv_4 = "" #"mat4 inverse(mat4 m) {\n   m[0][0] = -m[0][0];\n   m[1][0] = -m[1][0];\n   m[2][0] = -m[2][0]; \n  m[3][0] = -m[3][0];\n   m[0][1] = -m[0][1];\n   m[1][1] = -m[1][1];\n   m[2][1] = -m[2][1]; \n  m[3][1] = -m[3][1];\n   m[0][2] = -m[0][2];\n   m[1][2] = -m[1][2];\n   m[2][2] = -m[2][2]; \n  m[3][2] = -m[3][2];\n   m[0][3] = -m[0][3];\n   m[1][3] = -m[1][3];\n   m[2][3] = -m[2][3]; \n  m[3][3] = -m[3][3];\nreturn m;\n}\n"
#Position Attribute
                attributes = '\n'.join([
                'in vec3 position;',
                'in vec3 normal;',
                'in vec2 uv;',
                '\n'
                ]);
                o_attributes = '\n'.join([
                'out vec4 position;',
                'out vec3 normal;',
                'out vec2 uv;',
                '\n'
                ]);
                output_material['fragmentShader'] = "#version 300 es\n#extension GL_OES_standard_derivatives : enable\nprecision mediump float;\n"+attributes+inv_4+"#define VERTEX_TEXTURES\n#define GAMMA_FACTOR 2\n#define MAX_BONES 0\n#define BONE_TEXTURE\n#define NUM_CLIPPING_PLANES 0\nuniform mat4 modelMatrix;\nuniform mat4 modelViewMatrix;\nuniform mat4 projectionMatrix;\nuniform mat3 normalMatrix;\n" + output_material['fragmentShader']
                output_material['vertexShader'] = "#version 300 es\nprecision mediump float;\n" + "#define VERTEX_TEXTURES\n#define GAMMA_FACTOR 2\n#define MAX_BONES 0\n#define BONE_TEXTURE\n#define NUM_CLIPPING_PLANES 0\nuniform mat4 modelMatrix;\nuniform mat4 modelViewMatrix;\nuniform mat4 projectionMatrix;\nuniform mat3 normalMatrix;\n" +o_attributes + output_material['vertexShader']
                attributes = shader_details['attributes']
                uniforms = shader_details['uniforms']

                for uni in uniforms:
                    def uni_matrix4():
                        output_material['uniforms'][uni['varname']] = { "type":"m4", "value": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] }  
                    def uni_vector4():
                        output_material['uniforms'][uni['varname']]= { "type":"v4", "value": [0,0,0,0] }
                    def uni_vector3():
                        output_material['uniforms'][uni['varname']]= { "type":"v3", "value": [0,0,0] }
                    def uni_float():
                        output_material['uniforms'][uni['varname']]= { "type":"f", "value": 0.0 }
                    def uni_vector2():
                        output_material['uniforms'][uni['varname']]= { "type":"v2", "value": [0,0] }
                        
                    def uni_int():
                        output_material['uniforms'][uni['varname']]= { "type":"i", "value": 0 }
                    def uni_texture():
                        output_material['uniforms'][uni['varname']]= { "type":"t", "value": get_texture_uuid(uni['image']) }
                    def uni_FIXME():
                        # okay.
                        return
                    switch = { 
                    
#Next, need to go through each of these fucking things, and tell threejs where to look it all up at. Not everything is going to be 'initialize to default value and leave it there', most things
#will need to be updated with their values from three.
                        gpu.GPU_DYNAMIC_OBJECT_VIEWMAT:           uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_OBJECT_MAT:               uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_OBJECT_VIEWIMAT:          uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_OBJECT_IMAT:              uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_LAMP_DYNIMAT:             uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_LAMP_DYNPERSMAT:          uni_matrix4,  # matrix 4x4
                        gpu.GPU_DYNAMIC_OBJECT_COLOR:             uni_vector4,  # vector4
                        gpu.GPU_DYNAMIC_LAMP_DYNVEC:              uni_vector3,  # vector3
                        gpu.GPU_DYNAMIC_LAMP_DYNCO:               uni_vector3,  # vector 3
                        gpu.GPU_DYNAMIC_LAMP_DYNCOL:              uni_vector3,  # vector3
                        gpu.GPU_DYNAMIC_LAMP_DYNENERGY:           uni_float,    # float
                        gpu.GPU_DYNAMIC_SAMPLER_2DSHADOW:         uni_texture,  # float 
                        gpu.GPU_DYNAMIC_SAMPLER_2DBUFFER:         uni_texture,  # int representing texture
                        gpu.GPU_DYNAMIC_SAMPLER_2DIMAGE:          uni_texture,  # int representing texture loaded from image
                        gpu.GPU_DYNAMIC_OBJECT_AUTOBUMPSCALE:     uni_int,       # int
                        
# https://docs.blender.org/api/blender_python_api_2_78_4/gpu.html

                        gpu.GPU_DYNAMIC_OBJECT_LOCTOVIEWIMAT: uni_matrix4,
                        gpu.GPU_DYNAMIC_OBJECT_LOCTOVIEWMAT: uni_matrix4,                        
                        
                        gpu.GPU_DYNAMIC_AMBIENT_COLOR: uni_vector3,
                        gpu.GPU_DYNAMIC_HORIZON_COLOR: uni_vector3,
                        
                        gpu.GPU_DYNAMIC_MAT_SPEC: uni_float,
                        
                        gpu.GPU_DYNAMIC_MAT_SPECRGB: uni_vector3,
                        gpu.GPU_DYNAMIC_MAT_DIFFRGB: uni_vector3,
                        
                        gpu.GPU_DYNAMIC_MAT_EMIT: uni_float,
                        gpu.GPU_DYNAMIC_MAT_ALPHA: uni_float,
                        gpu.GPU_DYNAMIC_MAT_AMB: uni_float,
                        gpu.GPU_DYNAMIC_MAT_REF: uni_float,
                        gpu.GPU_DYNAMIC_MAT_HARD: uni_float,                        

                        gpu.GPU_DYNAMIC_LAMP_ATT1: uni_float,
                        gpu.GPU_DYNAMIC_LAMP_ATT2: uni_float,
                        

                        
                        #gpu.GPU_DYNAMIC_LAMP: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_MAT: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_MISC: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_MIST: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_OBJECT: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_SAMPLER: uni_FIXME,
                        gpu.GPU_DYNAMIC_GROUP_WORLD: uni_FIXME,
                        
                        
                        

                        gpu.GPU_DYNAMIC_LAMP_DISTANCE: uni_float,
                        gpu.GPU_DYNAMIC_LAMP_SPOTBLEND: uni_float,
                        gpu.GPU_DYNAMIC_LAMP_SPOTSCALE: uni_vector2,
                        gpu.GPU_DYNAMIC_LAMP_SPOTSIZE: uni_float,
                        

                        
                        
                        gpu.GPU_DYNAMIC_MIST_COLOR: uni_vector4,
                        gpu.GPU_DYNAMIC_MIST_DISTANCE: uni_float,
                        gpu.GPU_DYNAMIC_MIST_ENABLE: uni_float,
                        gpu.GPU_DYNAMIC_MIST_INTENSITY: uni_float,
                        gpu.GPU_DYNAMIC_MIST_START: uni_float,
                        gpu.GPU_DYNAMIC_MIST_TYPE: uni_float,

                        gpu.GPU_DYNAMIC_NONE: uni_FIXME,

                        gpu.GPU_DYNAMIC_ZENITH_COLOR: uni_FIXME

                        
                        
                        
                        
                        
                    }
                    if uni['type'] in switch:
                        switch[uni['type']]()
                    else:
                        print("WARNING: Type: " + str(uni['type']) + " not understood.. gpu shader export.")
            else:
                output_material = {
                    'skinning':skin,
                    'blending':"NormalBlending",
                    'depthTest': True,
                    'uuid': str(uuid.uuid4()),
                    'map': None,
                    #'opacity': material.alpha,
                    'specular': color_helper(material.specular_color), 
                    'vertexColors': 0,
                    'color': color_helper(material.diffuse_color),
                    'shininess': 100 - (material.specular_hardness if material.specular_hardness <= 100 else 100),#  (specular_hardness <=100 ? specular_hardness : 100),#opposite of Hardness. max hardness is 511. Things will come out shiney by default >..<
                    'depthWrite': True,
                    'name': material.name,
                    'type': "MeshPhongMaterial",
                    'emissive': material.emit,
                    'side': 2,
                    'userData': {}
                }
            if(material.alpha != 1):
                output_material['opacity'] = material.alpha
                output_material['transparent'] = True
            
            parse_custom_props(material, output_material['userData'])

            #print(len(my_textures) )
            #print(my_textures)
            default_texture = {
                "minFilter": 1008,
                "magFilter": 1006,
                "uuid": str(uuid.uuid4()),
                "anisotropy": 1,
                "image": None,
                "mapping": 300,
                "repeat": [1,1],
                "wrap": [1000,1000]
            }
            
            if(len(my_textures) == 1):
                default_texture['image'] = my_textures[0]
                output_material['map'] = default_texture['uuid']
                output_json['textures'].append(default_texture)
                
            if(len(my_textures) > 1):
                #print("len_mytextures")
                #print(len(my_textures))
                
                if( not (use_shader_materials == True)):

                    new_output = {
                        'skinning':False,
                        'blending':"NormalBlending",
                        'uuid':str(uuid.uuid4()),
                        'type':"MultiMaterial",
                        'side':2,
                        'name':material.name,
                        'materials':[]
                    }
                    for t in my_textures:
                        nm = dict(output_material)
                        nm['uuid'] = str(uuid.uuid4())
                        nt = dict(default_texture)
                        nt['uuid'] = str(uuid.uuid4())
                        nt['image'] = t
                        output_json['textures'].append(nt)
                        nm['map'] = nt['uuid'] #t.uuid
                        new_output['materials'].append(nm)
                    output_material = new_output
            output_json['materials'].append(output_material)
            materials.append(output_material['uuid'])
            return output_material['uuid']

        for i in scene_json['children']: #output_json['object']:
            if( i['name']  == mesh.name):
                return False
        
        geom = parse_geometry(mesh)
        materials = [] 
        iter(mesh.data.materials, parse_material, materials)
        # Need to create a default material.
        
        output_object = {
            'name':mesh.name,
            'uuid':str(uuid.uuid4()),
            'matrix': parse_matrix(mesh.matrix_local),
            'visible':mesh.is_visible(scene),
            'type':"Mesh",
            'material': None if len(materials) == 0 else materials[0],
            'geometry':geom,
            'castShadow':True,
            'receiveShadow':True,
            'userData': {}
            
        }
        parse_custom_props(mesh, output_object['userData']);
        
        return output_object
    

   
    def scene_parse(i, o):

        try:
            t = i.type
        except:
            return
        if(not i.is_visible(scene)): return
        if(i.type == "LAMP"):
            parse_light(i)
        if(i.type == "MESH"):
            
            deselect_all_mesh()
            i.select = True
            #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            if(Apply_Mesh_Transforms == True):
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            pm = parse_mesh(i)
            if(pm != False):
                scene_json['children'].append(pm)
                
                

    iter(export_objs, scene_parse, None)

    output_json['object'] = scene_json

    #print ("Creating /tmp/blender_tmp.dump")

    #f = open('/tmp/blender_tmp.dump', 'w')
    #f.write( str_dump(output_json).replace("\\n","").replace("\\","\\\\").replace("\n",""))
    #f.close()

    #print("Testing " + output_dir + "/"+ output_filename)

    file_output = str(json.dumps(output_json, indent=3))#.replace("\\n",""))
    if(do_cache == True and os.path.exists(output_dir+"/"+output_filename)):
        f = open(output_dir+"/"+output_filename, 'r')
        r_file = str(f.read())
        import re
        import difflib
        
        reg = r"[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}"
        r_file = re.sub(reg, '', r_file)
        file_output_test = re.sub(reg, '', file_output)
        
        

        #f = open('/tmp/blender_tmp.dump', 'w')
        #f.write('\n'.join(list(difflib.unified_diff(r_file.splitlines(1),file_output_test.splitlines(1))) ))
        #f.close()
        #print('dumped diff to /tmp/blender_tmp.dump')        
        #print(len(file_output_test.splitlines(1)))
        #print(len(r_file.splitlines(1)))
        #print(file_output_test == r_file)
        if file_output_test == r_file:
            #print(file_output_test)
            
            print(output_filename + " Cached..")
            return

    
    #import difflib
    #print('\n'.join(difflib.ndiff(r_file.splitlines(1),file_output.splitlines(1))))
    #dump(r_file)

    print("Creating or Updating" + output_dir + "/"+ output_filename)
    
    f = open(output_dir+"/"+output_filename, 'w')
    final_output_string = json.dumps(output_json, indent=1)#.replace("\\n","")

    f.write(file_output)
    f.close()

    print("File size indented:")
    print(len(final_output_string))


    final_output_string = json.dumps(output_json)#.replace("\\n","")
    print("Uploaded File size (non-indented):")
    print(len(final_output_string))
    if(do_server_file_upload):
        print("Uploading to server...")
        server_file_upload(final_output_string,prop_server_id_number)



    #print("....done...")

def armature_apply_transforms(i,o):
    try:
        t = i.type
    except:
        return
    if(i.type == "ARMATURE"):
        deselect_all_mesh()
        i.select = True
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        print('Applied Armature')
    else:
        print('fawk ' + i.type)

iter(scene.objects, armature_apply_transforms, None)

def start():
    chunked_exporter(0, scene.objects,{'x':0,'y':0,'z':0})


start()