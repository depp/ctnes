import argparse
import numpy
import os

def read_pal(path):
    with open(path, 'rb') as fp:
        data = fp.read()
    n = len(data) // 3
    return numpy.frombuffer(data, numpy.uint8).reshape((n, 3))

def write_gpl(path, data):
    with open(path, 'w') as fp:
        print('GIMP Palette', file=fp)
        print('Name: ', os.path.basename(path), file=fp)
        print('Columns: 16', file=fp)
        print('#', file=fp)
        for col in data:
            print('{0[0]:3d} {0[1]:3d} {0[2]:3d}'.format(col), file=fp)

def main():
    p = argparse.ArgumentParser('pal2gpl')
    p.add_argument('input', help='input PAL file')
    p.add_argument('output', nargs='?', help='output GPL file')
    args = p.parse_args()
    pal = read_pal(args.input)
    output = args.output
    if output is None:
        base, ext = os.path.splitext(args.input)
        output = base + '.gpl'
    write_gpl(output, pal)

if __name__ == '__main__':
    main()
