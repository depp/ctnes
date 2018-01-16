import numpy

def make_pattern(sprites):
    """Convert an array of sprites to PPU pattern data.

    The input should have shape (n,8,8) or (n,16,8) and type uint8.
    """
    if sprites.dtype != numpy.uint8:
        raise TypeError('bad sprite type: {}'.format(sprites.dtype))
    n, h, w = sprites.shape
    if w != 8:
        raise ValueError('bad sprite dimensions: {}x{}'.format(w, h))
    if h == 8:
        pass
    elif h == 16:
        sprites = sprites.reshape((-1, 8, 8))
    else:
        raise ValueError('bad sprite dimensions: {}x{}'.format(w, h))
    d = sprites[:,None] >> numpy.array([0, 1], numpy.uint8)[None,:,None,None]
    d &= 1
    return numpy.packbits(d, axis=3).tobytes()

def print_data(dtype, data, fp):
    a = numpy.array(data, dtype)
    bad, = numpy.nonzero(data != a)
    if bad:
        raise ValueError('value {} at index {} does not fit in {}',
                         data[bad[0]], bad[0], dtype)
    if dtype == numpy.uint8:
        directive = '.byte'
    elif dtype == numpy.int8:
        a = a.view(numpy.uint8)
        directive = '.byte'
    else:
        raise ValueError('unknown type {}'.format(dtype))
    width = 80
    pos = 0
    for x in a:
        s = str(x)
        if pos + 1 + len(s) > width:
            fp.write('\n')
            pos = 0
        if pos == 0:
            fp.write('\t')
            fp.write(directive)
            pos = 8 + len(directive)
            sep = ' '
        fp.write(sep)
        fp.write(s)
        pos += 1 + len(s)
        sep = ','
    if pos:
        fp.write('\n')
