MEMORY {
    ZP:     start = $0000, size = $0100, type = rw;
    RAM:    start = $0300, size = $0400, type = rw;
    HEADER: start = $0000, size = $0010, type = rw, file = %O, fill = yes;
    PRG0:   start = $8000, size = $4000, type = ro, file = %O, fill = yes;
    CHR0:   start = $0000, size = $2000, type = ro, file = %O, fill = yes;
}

SEGMENTS {
    ZEROPAGE: load = ZP, type = zp;
    BSS:    load = RAM, type = bss;
    INES:   load = HEADER, type = ro, align = $10;
    CODE:   load = PRG0, type = ro;
    VECTOR: load = PRG0, type = ro, start = $BFFA;
    CHR0:   load = CHR0, type = ro;
}
