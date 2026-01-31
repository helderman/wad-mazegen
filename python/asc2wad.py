# asc2wad.py - convert a maze from ASCII to WAD
# Ruud Helderman, January 2026 - MIT License

import argparse
import re
import struct
import sys
from itertools import zip_longest
from typing import NamedTuple
import matplotlib.pyplot as plt

width_pass = 128
width_pole = 32

xpos = []
ypos = []
vertex_hash = {}
vertex_list = []
linedef_list = []
thing_list = []

class CharSpan(NamedTuple):
    value: str
    start: int
    end: int

class Linedef(NamedTuple):
    start: int
    end: int

def get_vertex_index(x, y):
    v = (xpos[x], ypos[y])
    if v in vertex_hash:
        i = vertex_hash[v]
    else:
        i = len(vertex_hash)
        vertex_hash[v] = i
        vertex_list.append(v)
    return i

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

def draw_matplot():
    for x, y, t in thing_list:
        plt.plot(x, y, 'bo')
    for linedef in linedef_list:
        x1, y1 = vertex_list[linedef.start]
        x2, y2 = vertex_list[linedef.end]
        plt.plot([x1, x2], [y1, y2], marker='.', ms=2, mec='k', lw=1, color='silver')
    plt.show()

def write_umdf(filename, args):
    with open(filename, 'wb') as f:
        # PWAD header, 12 bytes: signature, number of lumps, offset of directory
        f.write(struct.pack('<4s2i', b'PWAD', 3, 12))

        # Three directory entries, 16 bytes each: lump offset, lump size, name
        f.write(struct.pack('<2i8s', 60, 0, b'MAP01'))
        f.write(struct.pack('<2i8s', 60, 0, b'TEXTMAP'))
        f.write(struct.pack('<2i8s', 60, 0, b'ENDMAP'))

        # UDMF boilerplate
        f.write(b'namespace = "zdoom";\n')

        # Things
        for x, y, t in thing_list:
            f.write(f'thing {{ x = {x}; y = {y}; angle = 90; type = {t}; skill1 = true; skill2 = true; skill3 = true; skill4 = true; skill5 = true; skill6 = true; skill7 = true; skill8 = true; single = true; coop = true; dm = true; class1 = true; class2 = true; class3 = true; class4 = true; class5 = true; }}\n'.encode('ascii'))

        # Vertices
        for x, y in vertex_list:
            f.write(f'vertex {{ x = {x}.0; y = {y}.0; }}\n'.encode('ascii'))

        # Linedefs
        for linedef in linedef_list:
            f.write(f'linedef {{ v1 = {linedef.start}; v2 = {linedef.end}; sidefront = 0; blocking = true; }}\n'.encode('ascii'))

        # Sidedef, sector
        f.write(f'sidedef {{ sector = 0; texturemiddle = "{args.texture_walls}"; }}\n'.encode('ascii'))
        f.write(f'sector {{ heightfloor = {args.height_floor}; heightceiling = {args.height_ceiling}; texturefloor = "{args.texture_floor}"; textureceiling = "{args.texture_ceiling}"; lightlevel = 192; }}\n'.encode('ascii'))

        # Fill in the blanks in the directory
        filesize = f.tell()
        f.seek(44)
        f.write(struct.pack('<i', filesize))
        f.seek(32)
        f.write(struct.pack('<i', filesize - 60))
        return filesize

def process_input(f):
    lines = [line.rstrip() for line in reversed(f.readlines())]
    process_walls(lines)
    process_things(lines)

def process_walls(lines):
    # Transpose twice
    cols = transpose_lines(lines)
    rows = transpose_lines(cols)

    # Calculate X coordinate between columns
    cs = get_char_spans(rows)
    for i in range(1, 1+len(rows[0])):
        xpos.append(max([xpos[c.start] + xsize(c.value) for c in cs if c.end == i], default=xpos[-1]))

    # Calculate Y coordinate between rows
    cs = get_char_spans(cols)
    for i in range(1, 1+len(cols[0])):
        ypos.append(max([ypos[c.start] + ysize(c.value) for c in cs if c.end == i], default=ypos[-1]))

    re_facing_negative = r'[^-+:|](?=[-+:|])'
    re_facing_positive = r'[-+:|](?=[^-+:|])'

    # Walls facing west
    for i, m in faces(rows, re_facing_negative):
        v1 = get_vertex_index(i, m.end())
        v2 = get_vertex_index(i, m.start())
        linedef_list.append(Linedef(v1, v2))

    # Walls facing east
    for i, m in faces(rows, re_facing_positive):
        v1 = get_vertex_index(i, m.start())
        v2 = get_vertex_index(i, m.end())
        linedef_list.append(Linedef(v1, v2))

    # Walls facing south
    for i, m in faces(cols, re_facing_negative):
        v1 = get_vertex_index(m.start(), i)
        v2 = get_vertex_index(m.end(), i)
        linedef_list.append(Linedef(v1, v2))

    # Walls facing north
    for i, m in faces(cols, re_facing_positive):
        v1 = get_vertex_index(m.end(), i)
        v2 = get_vertex_index(m.start(), i)
        linedef_list.append(Linedef(v1, v2))

def process_things(lines):
    for i, line in enumerate(lines):
        for m in re.finditer(r'\d+', line):
            x = (xpos[m.start()] + xpos[m.end()]) / 2
            y = (ypos[i] + ypos[i+1]) / 2
            t = int(m[0])
            thing_list.append((x, y, t))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ASCII maze to WAD file.')
    parser.add_argument('input', nargs='?', default='-', help='ASCII maze file.')
    parser.add_argument('-o', '--output', nargs='?', help='WAD file.')
    parser.add_argument('-p', '--plot', action='store_true', help='Plot map.')
    parser.add_argument('--offset-x', nargs='?', default=0, type=int, help='Offset X coordinate.')
    parser.add_argument('--offset-y', nargs='?', default=0, type=int, help='Offset Y coordinate.')
    parser.add_argument('--width-pass', nargs='?', default=128, type=int, help='Width of passages.')
    parser.add_argument('--width-pole', nargs='?', default=32, type=int, help='Width of poles.')
    parser.add_argument('--height-floor', nargs='?', default=0, type=int, help='Height of floor.')
    parser.add_argument('--height-ceiling', nargs='?', default=144, type=int, help='Height of ceiling.')
    parser.add_argument('--texture-floor', nargs='?', default='FLOOR0_1', help='Texture name for floor.')
    parser.add_argument('--texture-ceiling', nargs='?', default='F_SKY1', help='Texture name for ceiling.')
    parser.add_argument('--texture-walls', nargs='?', default='STARTAN1', help='Texture name for walls.')
    args = parser.parse_args()

    xpos.append(args.offset_x)
    ypos.append(args.offset_y)

    width_pass = args.width_pass
    width_pole = args.width_pole

    if args.input == '-':
        process_input(sys.stdin)
    else:
        with open(args.input, 'r') as f:
            process_input(f)

    print(len(vertex_list), 'vertices,', len(linedef_list), 'linedefs.', file=sys.stderr)

    if args.plot:
        draw_matplot()

    if args.output is not None:
        print('Written', write_umdf(args.output, args), 'bytes to WAD file.', file=sys.stderr)
