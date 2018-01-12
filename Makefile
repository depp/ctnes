objs := src/main.o src/data.o
out := ctnes.nes
map := map.txt

all: $(out)

clean:
	rm -f $(objs) $(out) $(map)

.PHONY: all clean

# Assemble

%.o: %.s
	ca65 $< -o $@

src/main.o: src/main.s src/defs.s src/charmap.s
src/data.o: src/data.s data/font.chr

# Link

ctnes.nes: src/main.x $(objs)
	ld65 -C src/main.x $(objs) -m map.txt -o $@
