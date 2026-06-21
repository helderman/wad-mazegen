# asc2wad.py - convert a maze from ASCII to WAD
# Ruud Helderman, January 2026 - MIT License

import argparse
import re
import struct
import sys
from itertools import zip_longest
from typing import NamedTuple
import matplotlib.pyplot as plt
import json

width_pass = 128
width_pole = 32

# Example: transpose_lines(["abcd", "1234", "xyz"]) ---> ["a1x", "b2y", "c3z", "d4+"]
def transpose_lines(ls):
    return [''.join(chars) for chars in zip_longest(*ls, fillvalue='+')]

def get_char_spans(data):
    return [CharSpan(m[0][0], m.start(), m.end()) for s in data for m in re.finditer(r'-+|\+|[:|]+|[^-+:|]+', s)]

def xsize(value):
    return width_pole if value in (':', '|', '+') else width_pass

def ysize(value):
    return width_pole if value in ('-', '+') else width_pass

def faces(lines, re_faces):
    ts = transpose_lines([re.sub(re_faces, '\t', line) for line in lines])
    return [(i, m) for i, t in enumerate(ts, start=1) for m in re.finditer(r'\t+', t)]

class CharSpan(NamedTuple):
    value: str
    start: int
    end: int

class Linedef(NamedTuple):
    start: int
    end: int

class Map:

    def __init__(self, mapname):
        self.mapname = mapname
        self.xpos = []
        self.ypos = []
        self.vertex_hash = {}
        self.vertex_list = []
        self.linedef_list = []
        self.thing_list = []

    def get_vertex_index(self, x, y):
        v = (self.xpos[x], self.ypos[y])
        if v in self.vertex_hash:
            i = self.vertex_hash[v]
        else:
            i = len(self.vertex_hash)
            self.vertex_hash[v] = i
            self.vertex_list.append(v)
        return i

    def draw_matplot(self):
        for x, y, t in self.thing_list:
            plt.plot(x, y, 'bo')
        for linedef in self.linedef_list:
            x1, y1 = self.vertex_list[linedef.start]
            x2, y2 = self.vertex_list[linedef.end]
            plt.plot([x1, x2], [y1, y2], marker='.', ms=2, mec='k', lw=1, color='silver')
        plt.show()

    def process_input(self, f, args):
        lines = [line.rstrip() for line in reversed(f.readlines())]
        self.xpos.append(args.offset_x)
        self.ypos.append(args.offset_y)
        self.process_walls(lines)
        self.process_things(lines)

    def process_walls(self, lines):
        # Transpose twice
        cols = transpose_lines(lines)
        rows = transpose_lines(cols)

        # Calculate X coordinate between columns
        cs = get_char_spans(rows)
        for i in range(1, 1+len(rows[0])):
            self.xpos.append(max([self.xpos[c.start] + xsize(c.value) for c in cs if c.end == i], default=self.xpos[-1]))

        # Calculate Y coordinate between rows
        cs = get_char_spans(cols)
        for i in range(1, 1+len(cols[0])):
            self.ypos.append(max([self.ypos[c.start] + ysize(c.value) for c in cs if c.end == i], default=self.ypos[-1]))

        re_facing_negative = r'[^-+:|](?=[-+:|])'
        re_facing_positive = r'[-+:|](?=[^-+:|])'

        # Walls facing west
        for i, m in faces(rows, re_facing_negative):
            v1 = self.get_vertex_index(i, m.end())
            v2 = self.get_vertex_index(i, m.start())
            self.linedef_list.append(Linedef(v1, v2))

        # Walls facing east
        for i, m in faces(rows, re_facing_positive):
            v1 = self.get_vertex_index(i, m.start())
            v2 = self.get_vertex_index(i, m.end())
            self.linedef_list.append(Linedef(v1, v2))

        # Walls facing south
        for i, m in faces(cols, re_facing_negative):
            v1 = self.get_vertex_index(m.start(), i)
            v2 = self.get_vertex_index(m.end(), i)
            self.linedef_list.append(Linedef(v1, v2))

        # Walls facing north
        for i, m in faces(cols, re_facing_positive):
            v1 = self.get_vertex_index(m.end(), i)
            v2 = self.get_vertex_index(m.start(), i)
            self.linedef_list.append(Linedef(v1, v2))

    def process_things(self, lines):
        for i, line in enumerate(lines):
            for m in re.finditer(r'\d+', line):
                x = (self.xpos[m.start()] + self.xpos[m.end()]) / 2
                y = (self.ypos[i] + self.ypos[i+1]) / 2
                t = int(m[0])
                self.thing_list.append((x, y, t))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ASCII maze to WAD file.')
    parser.add_argument('input', nargs='*', help='ASCII maze files')
    parser.add_argument('--udmf', nargs=1, help='Create WAD file (UDMF)')
    parser.add_argument('--babylon', nargs=1, help='Create HTML5 file (Babylon JS)')
    parser.add_argument('--matplot', action='store_true', help='Show drawing of first map (matplot)')
    parser.add_argument('--offset-x', nargs='?', default=0, type=int, help='offset X coordinate')
    parser.add_argument('--offset-y', nargs='?', default=0, type=int, help='offset Y coordinate')
    parser.add_argument('--width-pass', nargs='?', default=128, type=int, help='width of passages')
    parser.add_argument('--width-pole', nargs='?', default=32, type=int, help='width of poles')
    parser.add_argument('--height-floor', nargs='?', default=0, type=int, help='height of floor')
    parser.add_argument('--height-ceiling', nargs='?', default=144, type=int, help='height of ceiling')
    parser.add_argument('--texture-floor', nargs='?', default='FLOOR0_1', help='texture name for floor')
    parser.add_argument('--texture-ceiling', nargs='?', default='F_SKY1', help='texture name for ceiling')
    parser.add_argument('--texture-walls', nargs='?', default='STARTAN1', help='texture name for walls')
    args = parser.parse_args()

    width_pass = args.width_pass
    width_pole = args.width_pole

    maps = []
    if args.input:
        for i, name in enumerate(args.input):
            m = Map(f"MAP{i+1:02}")
            if name == '-':
                m.process_input(sys.stdin, args)
            else:
                with open(name, 'r') as f:
                    m.process_input(f, args)
            maps.append(m)
            print(m.mapname, ':', len(m.vertex_list), 'vertices,', len(m.linedef_list), 'linedefs.', file=sys.stderr)
            if args.matplot:
                m.draw_matplot()
    else:
        m = Map("MAP01")
        m.process_input(sys.stdin, args)
        maps.append(m)
        print(m.mapname, ':', len(m.vertex_list), 'vertices,', len(m.linedef_list), 'linedefs.', file=sys.stderr)
        if args.matplot:
            m.draw_matplot()

    if args.udmf is not None:
        with open(args.udmf[0], 'wb') as f:
            # PWAD header, 12 bytes: signature, number of lumps, offset of directory
            f.write(struct.pack('<4s2i', b'PWAD', 3 * len(maps), 12))

            for m in maps:
                # Three directory entries, 16 bytes each: lump offset, lump size, name
                f.write(struct.pack('<2i8s', 0, 0, m.mapname.encode('ascii')))
                f.write(struct.pack('<2i8s', 0, 0, b'TEXTMAP'))
                f.write(struct.pack('<2i8s', 0, 0, b'ENDMAP'))

            dir_offset = 12
            lump_offset = 12 + 48 * len(maps)

            for m in maps:
                # UDMF boilerplate
                f.write(b'namespace = "zdoom";\n')

                # Things
                for x, y, t in m.thing_list:
                    f.write(f'thing {{ x = {x}; y = {y}; angle = 90; type = {t}; '
                            .encode('ascii'))
                    if t == 17:                                        # picking up cell charge pack
                        f.write(f'special = 243; '.encode('ascii'))    # will end the level

                    f.write(f'skill1 = true; skill2 = true; skill3 = true; skill4 = true; skill5 = true; skill6 = true; skill7 = true; skill8 = true; single = true; coop = true; dm = true; class1 = true; class2 = true; class3 = true; class4 = true; class5 = true; }}\n'
                            .encode('ascii'))

                # Vertices
                for x, y in m.vertex_list:
                    f.write(f'vertex {{ x = {x}.0; y = {y}.0; }}\n'.encode('ascii'))

                # Linedefs
                for linedef in m.linedef_list:
                    f.write(
                        f'linedef {{ v1 = {linedef.start}; v2 = {linedef.end}; sidefront = 0; blocking = true; }}\n'.encode(
                            'ascii'))

                # Sidedef, sector
                f.write(f'sidedef {{ sector = 0; texturemiddle = "{args.texture_walls}"; }}\n'.encode('ascii'))
                f.write(
                    f'sector {{ heightfloor = {args.height_floor}; heightceiling = {args.height_ceiling}; texturefloor = "{args.texture_floor}"; textureceiling = "{args.texture_ceiling}"; lightlevel = 192; }}\n'.encode(
                        'ascii'))

                # Fill in the blanks in the directory
                lump_size = f.tell() - lump_offset
                f.seek(dir_offset)
                f.write(struct.pack('<i', lump_offset))
                dir_offset += 16
                f.seek(dir_offset)
                f.write(struct.pack('<2i', lump_offset, lump_size))
                dir_offset += 16
                lump_offset += lump_size
                f.seek(dir_offset)
                f.write(struct.pack('<i', lump_offset))
                dir_offset += 16
                f.seek(lump_offset)

            print('Written', f.tell(), 'bytes to WAD file.', file=sys.stderr)

    if args.babylon is not None:
        with open(args.babylon[0], 'wt') as f:
            f.write('''<!DOCTYPE html>
<meta charset="utf-8">
<title>Maze preview</title>
<style>
html, body { width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden; }
#maze { width: 100%; height: 100%; touch-action: none; }
#mapselect { position: absolute; left: 0.5em; top: 0.5em; z-index: 1; }
</style>
<canvas id="maze"></canvas>
<select id="mapselect"></select>
<script src="https://cdn.babylonjs.com/babylon.js"></script>
<script>
const canvas = document.getElementById('maze');
const mapselect = document.getElementById('mapselect');
const engine = new BABYLON.Engine(canvas, true, {preserveDrawingBuffer: true, stencil: true});
function createScene(things, vertices, linedefs) {
    const scene = new BABYLON.Scene(engine);
    scene.gravity = new BABYLON.Vector3(0, -1, 0);
    scene.collisionsEnabled = true;
    const camera = new BABYLON.UniversalCamera('cam', new BABYLON.Vector3(0, 5, -10)); // TODO
    camera.cameraDirection = new BABYLON.Vector3(0, 0, 0.5);
    camera.attachControl(canvas, false);
    camera.ellipsoid = new BABYLON.Vector3(3, 2, 3);
    camera.applyGravity = true;
    camera.checkCollisions = true;
    new BABYLON.HemisphericLight('light1', BABYLON.Vector3.Up()).diffuse = new BABYLON.Color3(0.4, 0.6, 0.8);
    const vposVertexShader = 'precision highp float;attribute vec3 position;uniform mat4 worldViewProjection;varying vec3 vPos;void main(){gl_Position=worldViewProjection*vec4(vPos=position,1);}';
    const woodFragmentShader = 'precision highp float;varying vec3 vPos;void main(){float x=vPos.x+vPos.z,d=1.-.05*sin(x*.15+fract(x*.2));gl_FragColor=vec4(vec3(.6,.44,.2)*d*(1.+.05*fract(vPos.y*.05+sin(x*.2+d)*20.)),1);}';
    const carpetFragmentShader = 'precision highp float;varying vec3 vPos;void main(){gl_FragColor=vec4(.4,step(1.,dot(fract(vPos.xz+sin(vPos.zx)),vec2(1)))*.2,.2,1);}';
    const wood = new BABYLON.ShaderMaterial('wood', scene, {vertexSource: vposVertexShader, fragmentSource: woodFragmentShader}, {});
    const ground = BABYLON.MeshBuilder.CreateGround("ground1", { width: 999, height: 999 });
    ground.checkCollisions = true;
    ground.material = new BABYLON.ShaderMaterial('carpet', scene, {vertexSource: vposVertexShader, fragmentSource: carpetFragmentShader}, {});
    for (const thing of things) {
        const x = thing[0]/8;
        const y = thing[1]/8;
        switch (thing[2]) {
            case 1:   // start position of player (= camera)
                camera.position = new BABYLON.Vector3(x, 4, y);
                break;
            default:  // objects
                BABYLON.MeshBuilder.CreateSphere('sphere1', {diameter: 2}).position = new BABYLON.Vector3(x, 1, y);
        }
    }
    for (const linedef of linedefs) {
        const start = vertices[linedef[0]];
        const end   = vertices[linedef[1]];
        const x1 = start[0]/8, x2 = end[0]/8;
        const y1 = start[1]/8, y2 = end[1]/8;
        const plane = BABYLON.MeshBuilder.CreatePlane('plane', {width: Math.abs(x1-x2+y1-y2), height: 10, sourcePlane: BABYLON.Plane.FromPoints(new BABYLON.Vector3(x1, 0, y1), new BABYLON.Vector3(x2, 0, y2), new BABYLON.Vector3(x2, -1, y2))});
        plane.position = new BABYLON.Vector3((x1+x2)/2, 5, (y1+y2)/2);
        plane.checkCollisions = true;
        plane.material = wood;
    }
    return scene;
}
function addOption(name) {
    const opt = document.createElement("option");
    opt.innerText = opt.value = name;
    mapselect.appendChild(opt);
}
const scenes = {};
'''
            );
            for m in maps:
                f.write(f'addOption("{m.mapname}");\n');
                f.write(f'scenes["{m.mapname}"] = createScene({json.dumps(m.thing_list)}, {json.dumps(m.vertex_list)}, {json.dumps(m.linedef_list)});\n');
            f.write('''
engine.runRenderLoop(function() { scenes[mapselect.value].render(); });
window.addEventListener('resize', function() { engine.resize(); });
</script>
'''
            );
            print('Written', f.tell(), 'bytes to HTML file.', file=sys.stderr)
