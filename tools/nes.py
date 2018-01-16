import numpy
import os

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

def nes_palette():
    global _nes_palette
    try:
        return _nes_palette
    except NameError:
        pass
    palpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'palette.gpl')
    with open(palpath) as fp:
        for line in fp:
            if line.startswith('#'):
                break
        pal = numpy.zeros((256, 3), numpy.uint8)
        n = 0
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            rgb = line.split()[:3]
            for i in range(3):
                pal[n,i] = int(rgb[i])
            n += 1
        pal = pal[:n]
    _nes_palette = pal
    return pal

class DataWriter:
    """DataWriter writes data to an assembly file as .incbin statements."""
    def __init__(self, asmpath, datpath):
        asmfp, datfp = None, None
        try:
            asmfp = open(asmpath, 'w')
            datfp = open(datpath, 'wb')
            self.asmfp = asmfp
            self.datfp = datfp
            self.pos = 0
            self.amt = 0
            self.datname = os.path.basename(datpath)
        except:
            if asmfp is not None:
                asmfp.close()
            if datfp is not None:
                datfp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.flush()
        self.asmfp.close()
        self.datfp.close()

    def flush(self):
        if not self.amt:
            return
        self.asmfp.write('.incbin "{}", {}, {}\n'.format(
            self.datname, self.pos, self.amt))
        self.pos += self.amt
        self.amt = 0

    def write_asm(self, text):
        self.flush()
        self.asmfp.write(text)

    def write(self, data):
        self.datfp.write(data)
        self.amt += len(data)
