import argparse
import lxml.etree as etree
import PIL.Image as image
import numpy
import os
import pathlib
import sys

import nes

def unknown_tag(elt, child):
    print('warning: unknown tag <{}> in <{}>'.format(child.tag, elt.tag),
          file=sys.stderr)

class TiledTileset:
    @classmethod
    def load(class_, inpath):
        with open(inpath, 'rb') as fp:
            doc = etree.parse(fp)
        self = class_()
        self.name = inpath
        self.source = None
        self.parse_tileset(doc.getroot())
        return self

    def parse_tileset(self, elt):
        if elt.tag != 'tileset':
            raise ValueError('got <{}>, expected <tileset>'.format(elt.tag))
        self.tilecount = int(elt.get('tilecount'))
        for child in elt:
            if child.tag == 'image':
                self.parse_image(child)
            else:
                unknown_tag(elt, child)

    def parse_image(self, elt):
        if self.source is not None:
            raise ValueError('multiple <image> tags')
        self.source = elt.get('source')

class Tilemap:
    @classmethod
    def load(class_, inpath):
        inpath = pathlib.Path(inpath).resolve()
        with open(inpath, 'rb') as fp:
            doc = etree.parse(fp)
        self = class_()
        self.parse_tilemap(doc.getroot())
        base = inpath.parent
        for n, (firstgid, src) in enumerate(self.tilesets):
            tset = TiledTileset.load(inpath.parent / src)
            self.tilesets[n] = firstgid, tset
        return self

    def parse_tilemap(self, elt):
        if elt.tag != 'map':
            raise ValueError('got <{}>, expected <map>'.format(elt.tag))
        width = int(elt.get('width'))
        height = int(elt.get('height'))
        self.size = (height, width)
        self.tiles = None
        self.attrs = None
        self.tilesets = []
        for child in elt:
            if child.tag == 'layer':
                self.parse_layer(child)
            elif child.tag == 'tileset':
                self.parse_tileset(child)
            elif child.tag == 'objectgroup':
                self.parse_objectgroup(child)
            else:
                unknown_tag(elt, child)
        if self.tiles is None:
            raise ValueError('no "tiles" layer')
        if self.attrs is None:
            raise ValueError('no "attributes" layer')

    def parse_layer(self, elt):
        data = None
        for child in elt:
            if child.tag == 'data':
                if data is not None:
                    raise ValueError('multiple <data> elements')
                data = self.parse_data(child)
            else:
                unknown_tag(elt, child)
        if data is None:
            raise ValueError('no <data> element')
        flips = data & (0b111 << 29)
        if numpy.any(flips):
            for loc in numpy.array(numpy.where(flips)).transpose():
                print('error: flipped tile at ({0[1]},{0[0]})'.format(loc),
                      file=sys.stderr)
            raise ValueError('some tiles are flipped')
        name = elt.get('name').lower()
        if name == 'tiles':
            if self.tiles is not None:
                raise ValueError('multiple "tiles" layers')
            self.tiles = data
        elif name == 'attributes':
            if self.attrs is not None:
                raise ValueError('multiple "attributes" layers')
            self.attrs = data
        else:
            raise ValueError('unknown layer {!r}'.format(name))

    def parse_data(self, elt):
        encoding = elt.get('encoding')
        if encoding != 'csv':
            raise ValueError('unknown encoding {!r}'.format(encoding))
        height, width = self.size
        data = numpy.zeros(self.size, numpy.uint32)
        lines = [line for line in elt.text.splitlines() if line]
        if len(lines) != height:
            raise ValueError('got {} rows, expected {}'
                             .format(len(lines), height))
        for y, line in enumerate(lines):
            row = numpy.fromstring(line, numpy.uint32, sep=',')
            if len(row) != width:
                raise ValueError('got {} columns, expected {}'
                                 .format(len(row), width))
            data[y] = row
        return data

    def parse_tileset(self, elt):
        firstgid = int(elt.get('firstgid'))
        source = elt.get('source')
        self.tilesets.append((firstgid, source))

    def parse_objectgroup(self, elt):
        pass

def tile_usage(tmaps):
    tsets = {}
    for tmap in tmaps:
        gids = tmap.tiles.flatten()
        maxgid = numpy.max(gids)
        gidset = numpy.zeros((maxgid+1,), numpy.bool)
        gidset[gids] = True
        for gid, tset in tmap.tilesets:
            if gid > maxgid:
                continue
            try:
                tset, usage = tsets[tset.name]
            except KeyError:
                usage = numpy.zeros((tset.tilecount,), numpy.bool)
                tsets[tset.name] = tset, usage
            subset = gidset[gid:]
            limit = min(len(subset), len(usage))
            usage[:limit] |= subset[:limit]
    return tsets

class Tileset:
    def __init__(self, usages):
        gid = 1
        self.tsets = {}
        self.tiles = [numpy.zeros((1, 8, 8), numpy.uint8)]
        for path in sorted(usages):
            tset, usage = usages[path]
            n = numpy.count_nonzero(usage)
            gidmap = numpy.zeros((tset.tilecount,), numpy.uint8)
            self.tsets[path] = gidmap
            if not n:
                continue
            img = image.open(tset.name.parent / tset.source)
            assert img.mode == 'P'
            img = numpy.array(img)
            pal = img[0,0:4]
            pmap = numpy.zeros((numpy.max(img)+1,), numpy.uint8)
            pmap[pal] = numpy.arange(0, 4, dtype=numpy.uint8)
            img = pmap[img]
            numpy.place(gidmap, usage,
                        numpy.arange(gid, gid + n, dtype=numpy.uint8))
            gid += n
            height, width = img.shape
            tiles = numpy.array(numpy.split(img, width//8, axis=1))
            tiles = numpy.concatenate(numpy.split(tiles, height//8, axis=1))
            tiles = tiles[usage]
            self.tiles.append(tiles)
        self.tiles = numpy.concatenate(self.tiles)

    def dump_pattern(self, fp):
        fp.write(nes.make_pattern(self.tiles))

class Level:
    def __init__(self, tmap, tset):
        self.init_tiles(tmap, tset)
        self.init_attrs(tmap)

    def init_tiles(self, tmap, tset):
        tiles = tmap.tiles
        gidmap = numpy.zeros((numpy.max(tiles) + 1,), numpy.uint8)
        for gid, tmtset in tmap.tilesets:
            try:
                src = tset.tsets[tmtset.name]
            except KeyError:
                continue
            dest = gidmap[gid:]
            limit = min(len(dest), len(src))
            dest[:limit] = src[:limit]
        self.tiles = gidmap[tiles]

    def init_attrs(self, tmap):
        height, width = tmap.size
        attrarr = tmap.attrs.reshape((height//2, 2, width//2, 2))
        minval = numpy.min(attrarr, axis=(1, 3))
        maxval = numpy.max(attrarr, axis=(1, 3))
        mismatch = minval != maxval
        if numpy.any(mismatch):
            for y, x in numpy.array(numpy.where(mismatch)).transpose():
                print('error: bad attribute block at ({},{})'
                      .format(y*2, x*2))
            raise ValueError('bad attribute blocks')
        example_gid = numpy.max(maxval)
        for gid, tset in tmap.tilesets:
            if gid <= example_gid < gid + tset.tilecount:
                break
        else:
            raise ValueError('could not find tileset for gid {}'
                             .format(example_gid))
        if tset.tilecount != 4:
            raise ValueError('attribute tileset {} has {} entries, want 4'
                             .format(tset.source, tset.tilecount))
        attrs = numpy.zeros((height//2, width//2), numpy.uint8)
        for i in range(1, 4):
            numpy.place(attrs, maxval == i+gid, i)
        self.attrs = attrs

    def dump_flat_data(self, fp):
        print(self.tiles.dtype, self.tiles.shape)
        fp.write(self.tiles.tobytes())
        attrs = numpy.pad(self.attrs, ((0, 1), (0, 0)), 'constant')
        print(attrs)
        attrs = attrs.reshape((8, 2, 8, 2))
        attrs = numpy.array(numpy.swapaxes(attrs, 1, 2))
        attrs = attrs.reshape((64, 4))
        attrs <<= numpy.arange(0, 8, 2, numpy.uint8)
        attrs = numpy.bitwise_or.reduce(attrs, axis=1)
        print(attrs.reshape(8, 8))
        fp.write(attrs.tobytes())

def main():
    p = argparse.ArgumentParser(
        'levels.py',
        description='Convert level data files.',
        allow_abbrev=False)
    p.add_argument('level')
    p.add_argument('-data-out', required=True)
    p.add_argument('-asm-out', required=True)

    args = p.parse_args()

    tmap = Tilemap.load(args.level)
    tset = Tileset(tile_usage([tmap]))
    level = Level(tmap, tset)
    with nes.DataWriter(args.asm_out, args.data_out) as fp:
        fp.write_asm('.segment "CHR0b"\n')
        tset.dump_pattern(fp)
        fp.write_asm(
            '.code\n'
            '.export leveldata\n'
            'leveldata:\n')
        level.dump_flat_data(fp)

if __name__ == '__main__':
    main()
