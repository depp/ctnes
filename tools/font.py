import PIL.Image as image
import numpy
import pathlib

def make_chr(sprites):
    """Convert an array of sprites to CHR data.

    The input should have shape (n,8,8) or (n,16,8) and type uint8.
    """
    n, h, w = sprites.shape
    if h not in (8, 16) or w != 8:
        raise ValueError('bad sprite dimensions: {}x{}'.format(w, h))
    d = sprites[:,None] >> numpy.array([0, 1], numpy.uint8)[None,:,None,None]
    d &= 1
    return numpy.packbits(d, axis=3).tobytes()

def main():
    srcdir = pathlib.Path(__file__).resolve().parent.parent
    inpath = srcdir / 'data/font.png'
    chrpath = inpath.with_suffix('.chr')
    mappath = srcdir / 'src/charmap.s'
    img = image.open(inpath)
    img = img.convert('L')
    img = numpy.where(img, numpy.uint8(1), numpy.uint8(0))
    glyphs = numpy.array(numpy.split(img, 16, axis=1))
    glyphs = numpy.concatenate(numpy.split(glyphs, 16, axis=1))
    exist = numpy.any(numpy.any(glyphs, axis=1), axis=1)
    exist[0] = True
    indexes, = numpy.nonzero(exist)
    glyphs = glyphs[indexes]
    bands = numpy.array([2, 2, 3, 3, 3, 2, 2, 2], numpy.uint8)
    hilite = numpy.where(glyphs, bands[None,:,None], numpy.uint8(0))
    shadow = numpy.roll(numpy.roll(glyphs, 1, axis=1), 1, axis=2)
    shadow[:,0,:] = 0
    shadow[:,:,0] = 0
    glyphs = numpy.where(hilite, hilite, shadow)
    data = make_chr(glyphs)
    chrpath.write_bytes(data)
    with mappath.open('w') as fp:
        for n, index in enumerate(indexes):
            index = int(index) + 32
            if index > 127:
                break
            print('.charmap ${:02x}, ${:02x}'.format(index, n), file=fp)

if __name__ == '__main__':
    main()
