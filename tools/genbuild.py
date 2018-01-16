import argparse
import ninja_syntax
import os
from pathlib import Path
import re
import sys

outfile = 'ctnes.nes'

buildfile = 'build.ninja'

top_asm = [
    'main.s',
    'data.s',
    'sprite.s',
]

include_re = r'(?im)^\s*\.(?:inc.*)\s+"([-./\w]+)"'

class Builder:
    def __init__(self, w, srcpath, buildpath):
        self.w = w
        self.incmap = {}
        self.srcpath = srcpath
        self.buildpath = buildpath
        self.generated = set()

    def genfiles(self, outputs, inputs, args):
        """Generate data or source files.

        Arguments:
        outputs -- list of Path
        inputs -- list of Path
        args -- arguments to pass to generator
        """
        self.generated.update(outputs)
        self.w.build(
            [str(path) for path in outputs],
            'gendata',
            [str(path) for path in inputs],
            variables=[('args', [str(arg) for arg in args])],
        )

    def includes(self, src, parents=None):
        """List the include dependencies for a source file.

        Arguments:
        src -- a Path
        """
        try:
            return self.incmap[src]
        except KeyError:
            pass
        result = set()
        if parents is None:
            parents = []
        if src in parents:
            raise ValueError('include loop')
        parents.append(src)
        print(src)
        text = src.read_text()
        for inc in re.findall(include_re, text):
            # Ugh
            incpath = Path(os.path.normpath(str(self.buildpath / inc)))
            if incpath in self.generated:
                result.add(incpath)
                continue
            incpath = Path(os.path.normpath(str(self.srcpath / inc)))
            result.add(incpath)
            result.union(self.includes(incpath, parents))
        self.incmap[src] = result
        parents.pop()
        return result

    def assemble(self, src):
        srcpath = self.srcpath / src
        objpath = (self.buildpath / src).with_suffix('.o')
        self.w.build(
            [str(objpath)],
            'asm',
            [str(srcpath)],
            implicit=[str(path) for path in sorted(self.includes(srcpath))],
        )
        return objpath

def main():
    p = argparse.ArgumentParser(
        'genbuild.py',
        description='Generate the Ninja build script for ctnes.',
        allow_abbrev=False)
    args = p.parse_args()

    root = Path(__file__).parent.parent
    oldcwd = Path.cwd()
    src = Path('src')
    tools = Path('tools')
    build = Path('build')
    data = Path('data')

    tmpfile = buildfile + '.tmp'
    with open(tmpfile, 'w') as fp:
        w = ninja_syntax.Writer(fp)
        b = Builder(w, src, build)

        # Rules
        w.rule('genbuild', [sys.executable] + sys.argv, generator=True)
        w.rule('gendata', [sys.executable, '$args'])
        w.rule('asm', [
            'ca65',
            '-I', str(build),
            '-I', str(src),
            '$in', '-o', '$out',
        ])
        w.rule('link',
               ['ld65', '-C', '$cfg', '$in', '-m', '$map', '-o', '$out'])
        w.build(
            ['build.ninja'],
            'genbuild',
            [sys.argv[0]],
        )

        # Generated files
        b.genfiles(
            [build/'font.dat', build/'charmap.s'],
            [data/'font.png', tools/'font.py', tools/'nes.py'],
            [
                tools/'font.py',
                '-font', data/'font.png',
                '-data-out', build/'font.dat',
                '-map-out', build/'charmap.s',
            ])
        b.genfiles(
            [build/'spritedata.dat', build/'spritedata.s'],
            [data/'hero.png', tools/'sprites.py', tools/'nes.py'],
            [
                tools/'sprites.py', 'compile', data/'hero.png',
                '-pattern-out', build/'spritedata.dat',
                '-asm-out', build/'spritedata.s',
            ])

        # Assembly files
        objs = []
        for path in top_asm:
            objs.append(b.assemble(path))

        # Outputs
        exepath = build/outfile
        mappath = build/'map.txt'
        cfgpath = src/'main.x'
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
