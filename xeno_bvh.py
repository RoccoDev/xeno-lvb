#  MIT License
#  
#  Copyright (c) 2024 RoccoDev
#  
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import argparse
import os
import sys
import struct
import json

from aabbtree import AABB, AABBTree

def u16(data): return struct.unpack('<H', data[0:2])[0]

def u32(data): return struct.unpack('<I', data[0:4])[0]

def f32(data): return struct.unpack('<f', data[0:4])[0]

def u64(data): return struct.unpack('<Q', data[0:8])[0]

def read_bvh(data, size):
    idx = 0

    nodes = []
    leaves = []

    while idx < size:
        min = [f32(data[idx + i * 4:]) for i in range(0, 3)]
        max = [f32(data[idx + 16 + i * 4:]) for i in range(0, 3)]
        aabb = AABB(list(zip(min, max)))
        parent = u64(data[idx + 0x20:])
        left = u64(data[idx + 0x28:])
        right = u64(data[idx + 0x30:])
        extra = u32(data[idx + 0x38:])
        has_extra = u32(data[idx + 0x3c:]) != 0

        parent = parent // 64 if parent != 0xFFFFFFFFFFFFFFFF else None
        left = left // 64 if left != 0xFFFFFFFFFFFFFFFF else None
        right = right // 64 if right != 0xFFFFFFFFFFFFFFFF else None
        node = AABBTree(aabb, value=extra if has_extra else None)
        nodes.append((parent, left, right, node))
        if has_extra:
            leaves.append(AABBTree(aabb, value=extra))

        idx += 64

    for (_, left, right, node) in nodes:
        node.left = nodes[left][3] if left else None
        node.right = nodes[right][3] if right else None
    return nodes[0][3], leaves

def write_bvh(tree):
    nodes = []

    q = [(tree, None, False)]
    while q:
        n, p, lr = q.pop()
        p_idx = len(nodes)
        nodes.append([p, n.aabb, n.value, None, None])
        if p is not None and p_idx != 0:
            if lr: # right
                nodes[p][4] = p_idx
            else:
                nodes[p][3] = p_idx
        if n.left is not None: q.append((n.left, p_idx, False))
        if n.right is not None: q.append((n.right, p_idx, True))

    size = len(nodes) * 64
    entry_buf = bytearray(size)
    idx = 0

    for i, [parent, aabb, value, left, right] in enumerate(nodes):
        x, y, z = aabb
        struct.pack_into("<ffffffffQQQII", entry_buf, idx, \
            x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, \
            parent * 64 if parent is not None else 0xFFFFFFFFFFFFFFFF, left * 64 if left is not None else 0xFFFFFFFFFFFFFFFF, \
            right * 64 if right is not None else 0xFFFFFFFFFFFFFFFF, value if value is not None else 0, 1 if value is not None else 0)
        idx += 64
    return entry_buf

def write_bvh_file(map_trees, file_out):
    for map_id, tree in map_trees:
        data = write_bvh(tree)
        file_out.write(bytes([0x47, 0x42, 0x56, 0x48]))
        file_out.write(struct.pack("<I", len(data) + 16))
        file_out.write(bytes([0x00, 0x01]))
        file_out.write(struct.pack("<H", map_id))
        file_out.write(bytes([0] * 4))
        file_out.write(data)

def read_bvh_file(file):
    file = bytes(file)
    total_size = len(file)
    idx = 0

    trees = {}

    while idx < total_size:
        assert list(file[idx:idx+4]) == [0x47, 0x42, 0x56, 0x48]
        assert list(file[idx+8:idx+10]) == [0x00, 0x01]
        size = u32(file[idx+4:])
        map_id = u16(file[idx+10:])

        trees[map_id] = read_bvh(file[idx+0x10:idx+size], size - 0x10)
        idx += size
    
    return trees

def cmd_extract(input, out):
    with open(input, "rb") as file:
        data = read_bvh_file(file.read())

    if not os.path.exists(out):
        os.mkdir(out)
    for map_id, (_, leaves) in data.items():
        with open(os.path.join(out, f"{map_id}.json"), 'wb') as f:
            j = json.dumps([{ 'id': f'<{leaf.value:08X}>', 'x': leaf.aabb.limits[0], 'y': leaf.aabb.limits[1], 'z': leaf.aabb.limits[2] } for leaf in leaves], \
                ensure_ascii=False, indent=1)
            f.write(j.encode('utf-8'))

def cmd_pack(input, out):
    maps = {}
    for path in os.listdir(input):
        f = os.path.join(input, path)
        if os.path.isfile(f) and path.endswith(".json"):
            map_id = int(path.removesuffix(".json"))
            with open(f) as f:
                obj = json.loads(f.read())
                nodes = [(AABB([e['x'], e['y'], e['z']]), int(e['id'].strip("<>"), 16)) for e in obj]
                maps[map_id] = nodes
    
    for map_id, nodes in maps.items():
        rebuild = AABBTree()
        for node in nodes:
            rebuild.add(node[0], node[1])
        maps[map_id] = rebuild
        print(f"Done rebuilding map {map_id}")

    maps = list(maps.items())
    maps.sort(key=lambda e: e[0])

    with open(out, "wb") as new:
        write_bvh_file(maps, new)

def main(argv):
    parser = argparse.ArgumentParser(description='Xenoblade 3 BVH editor')
    parser.add_argument('-o', '--out', metavar='OUTPUT-DIR', required=True,
                        help='Output directory for BVH->JSON')
    parser.add_argument('mode', metavar='MODE',
                        help=('"extract" for BVH->JSON, "pack" for JSON->BVH'))
    parser.add_argument('input', metavar='INPUT',
                        help=('For BVH->JSON, path to the .bvh file. For JSON->BVH, path to the extracted directory'))
    args = parser.parse_args()
    
    # For DLC4 bvh
    # TODO: iterative aabbtree implementation / Rust
    sys.setrecursionlimit(10000)

    mode = args.mode.lower()
    if mode == "extract":
        cmd_extract(args.input, args.out)
    elif mode == "pack":
        cmd_pack(args.input, args.out)
    else:
        raise Exception("invalid mode")

if __name__ == '__main__':
    main(sys.argv)

    