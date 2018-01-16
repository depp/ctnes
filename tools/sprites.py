import attr
import argparse
import PIL.Image as image
import numpy

import nes

@attr.s
class Rect:
    x0 = attr.ib()
    y0 = attr.ib()
    x1 = attr.ib()
    y1 = attr.ib()

    def __call__(self, arr):
        return arr[self.y0:self.y1,self.x0:self.x1]

@attr.s
class Part:
    xoff = attr.ib()
    yoff = attr.ib()
    sprite = attr.ib()

def find_sprite(arr):
    """Find bounding box of a single sprite in a 2D boolean array."""
    rows = numpy.argwhere(numpy.amax(arr, axis=1))
    cols = numpy.argwhere(numpy.amax(arr, axis=0))
    return Rect(int(numpy.amin(cols)), int(numpy.amin(rows)),
                int(numpy.amax(cols)) + 1, int(numpy.amax(rows)) + 1)

def find_sprites(arr):
    """Find bounding boxes of sprites in a 2D boolean array."""
    rows, = numpy.amax(arr, axis=1),
    rows = numpy.pad(rows, 1, 'constant')
    ranges = numpy.nonzero(rows[:-1] != rows[1:])[0].reshape(-1, 2)
    for ymin, ymax in ranges:
        rarr = arr[ymin:ymax]
        cols, = numpy.amax(rarr, axis=0),
        cols = numpy.pad(cols, 1, 'constant')
        cranges = numpy.nonzero(cols[:-1] != cols[1:])[0].reshape(-1, 2)
        for xmin, xmax in cranges:
            yield Rect(int(xmin),int(ymin),
                       int(xmax),int(ymax))

def find_mark(arr):
    """Find the coordinates of a sprite mark from a 2D boolean array."""
    a = arr.astype(numpy.uint16)
    xvals, = numpy.where(numpy.sum(a, axis=0) > 1)
    yvals, = numpy.where(numpy.sum(a, axis=1) > 1)
    if len(xvals) != 1 or len(yvals) != 1:
        raise ValueError('cannot find mark')
    return int(xvals[0]) + 1, int(yvals[0]) + 1

class Sprites:
    @classmethod
    def load(class_, inpath):
        img = image.open(inpath)
        assert img.mode == 'P'
        img = numpy.array(img)
        mark = img[0,0]
        ncolors = numpy.amax(img)
        # Transparent must be palette index 0.
        assert img[0,1] == 0
        # Get map from palette colors to 0..3 indexes.
        pcolors = img[:,0:3]
        pcolors = pcolors[numpy.where(numpy.amin(pcolors, axis=1))[0]]
        pmap = numpy.zeros((len(pcolors), ncolors), numpy.uint8)
        pmask = numpy.zeros((ncolors,), numpy.uint8)
        pmap[:,1:] = 0xff
        prange = numpy.arange(1, 4)
        for i in range(len(pcolors)):
            pmap[i][pcolors[i]] = prange
            pmask[pcolors[i]] |= 1 << i
        pmask[0] |= (1 << len(pcolors)) - 1
        # Convert each sprite.
        img = img[:,3:]
        pats = []
        sprites = []
        for sp in find_sprites(img != 0):
            # Sprite must be aligned vertically to 16 pixel grid.
            assert sp.y0 & 15 == 0
            sp = sp(img)
            spmark = sp == mark
            xorigin, yorigin = find_mark(spmark)
            sp = numpy.where(spmark, 0, sp)
            assert numpy.amax(sp[0]) == 0
            sp = numpy.pad(sp, [(0, 0), (0, 7)], 'constant')
            sprite = []
            for y in numpy.arange(1, img.shape[0], 16):
                rows = sp[y:y+16]
                cols = numpy.argwhere(numpy.amax(rows, axis=0))
                if cols.shape[0] == 0:
                    continue
                xmin = int(numpy.min(cols))
                xmax = int(numpy.max(cols)) + 1
                nsprite = (xmax - xmin + 7) // 8
                xmax = xmin + nsprite * 8
                rows = rows[:,xmin:xmax]
                smask = int(numpy.bitwise_and.reduce(
                    numpy.bitwise_and.reduce(pmask[rows])))
                for i in range(len(pmap)):
                    if (smask >> i) & 1:
                        rows = pmap[i,rows]
                        break
                else:
                    raise ValueError('too many colors')
                nsprite = (rows.shape[1] + 7) // 8
                for x in range(0, nsprite * 8, 8):
                    sprite.append(Part(
                        x + xmin - xorigin,
                        y - yorigin,
                        len(pats),
                    ))
                    pats.append(rows[:,x:x+8])
            sprites.append(sprite)
        self = class_()
        self.sprites = sprites
        self.patterns = numpy.array(pats)
        return self

    def write_pattern(self, fp):
        fp.write(nes.make_pattern(self.patterns))

    def write_asm(self, fp):
        sparr = numpy.zeros((len(self.sprites) + 1,), numpy.int32)
        n = 0
        for i, sprite in enumerate(self.sprites):
            sparr[i] = n
            n += len(sprite)
        sparr[len(self.sprites)] = n
        parr = numpy.zeros((3, n), numpy.int32)
        n = 0
        for sprite in self.sprites:
            for part in sprite:
                parr[0,n] = part.xoff
                parr[1,n] = part.yoff
                parr[2,n] = part.sprite
                n += 1
        if numpy.any(parr[2] > 255):
            raise ValueError('too many sprites')
        parr[2] = (parr[2] << 1) | (parr[2] >> 7)
        print('sprites:', file=fp)
        nes.print_data(numpy.uint8, sparr, fp)
        names = [
            ('xoffsets', numpy.int8),
            ('yoffsets', numpy.int8),
            ('indexes', numpy.uint8),
        ]
        for (name, dtype), data in zip(names, parr):
            print(name + ':', file=fp)
            nes.print_data(dtype, data, fp)

def main():
    p = argparse.ArgumentParser(
        'sprites.py',
        description='Convert game sprite files.',
        allow_abbrev=False)
    p.add_argument('-sprites', required=True)
    p.add_argument('-pattern-out', required=True)
    p.add_argument('-asm-out', required=True)
    args = p.parse_args()

    sprites = Sprites.load(args.sprites)
    with open(args.pattern_out, 'wb') as fp:
        sprites.write_pattern(fp)
    with open(args.asm_out, 'w') as fp:
        sprites.write_asm(fp)

if __name__ == '__main__':
    main()
