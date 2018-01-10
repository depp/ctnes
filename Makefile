all: ctnes.nes

src/main.o: $(wildcard src/*.s)
	ca65 src/main.s

ctnes.nes: src/main.o src/main.s
	ld65 -C src/main.x src/main.o -m map.txt -o $@
