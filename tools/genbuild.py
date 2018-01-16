import argparse
import ninja_syntax
import os
import pathlib
import re
import sys

outfile = 'ctnes.nes'

buildfile = 'build.ninja'

top_asm = [
    'main.s',
    'data.s',
]

class Builder:
    def __init__(self, w, srcdir, builddir):
        self.w = w
        self.srcdir = srcdir
        self.builddir = builddir
        self.incmap = {}
    def includes(self, src):
        try:
            return self.incmap[src]
        except KeyError:
            pass
    def assemble(self, src):
        inpath = self.srcdir / 'src' / src
        outpath = (self.builddir / 'obj' / src).with_suffix('.o')
        self.w.build(
            [str(outpath)],
            'asm',
            [str(inpath)],
        )
        return outpath

def main():
    srcdir = pathlib.Path(sys.argv[0]).parent.parent
    builddir = pathlib.Path('build')
    p = argparse.ArgumentParser(
        'genbuild.py',
        description='Generate the Ninja build script for ctnes.',
        allow_abbrev=False)
    args = p.parse_args()
    tmpfile = buildfile + '.tmp'
    with open(tmpfile, 'w') as fp:
        w = ninja_syntax.Writer(fp)
        w.rule('genbuild', [sys.executable] + sys.argv, generator=True)
        w.rule('asm', ['ca65', '$in', '-o', '$out'])
        w.rule('link',
               ['ld65', '-C', '$cfg', '$in', '-m', '$map', '-o', '$out'])
        w.build(
            ['build.ninja'],
            'genbuild',
            [sys.argv[0]],
        )
        b = Builder(w, srcdir, pathlib.Path('build'))
        objs = []
        for path in top_asm:
            objs.append(b.assemble(path))
        exepath = builddir / outfile
        mappath = builddir / 'map.txt'
        cfgpath = srcdir / 'src/main.x'
        w.build(
            [str(exepath)],
            'link',
            [str(path) for path in objs],
            implicit=[str(cfgpath)],
            implicit_outputs=[str(mappath)],
            variables=[
                ('map', str(mappath)),
                ('cfg', str(cfgpath)),
            ],
        )
    os.rename(tmpfile, buildfile)

if __name__ == '__main__':
    main()
