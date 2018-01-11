PPU_PAL0	= $3f00
PPU_NAME0	= $2000
PPU_ATTR0	= $23c0

; PPU registers.
PPUCTRL		= $2000
PPUMASK		= $2001
PPUSTATUS	= $2002
OAMADDR		= $2003
OAMDATA		= $2004
PPUSCROLL	= $2005
PPUADDR		= $2006
PPUDATA		= $2007

APUSTATUS	= $4015

.segment "INES"
.byte $4e, $45, $53, $1a
.byte 1		; Size of PRG in units of 16 KiB.
.byte 0		; Size of CHR in units of 8 KiB.
.byte 1		; Flags, vertical mirroring.

.code

reset:
	sei
	cld
	ldx #$ff
	txs
	inx
	stx PPUCTRL
	stx PPUMASK
	stx APUSTATUS

	; PPU warmup, wait two frames, plus a third later.
	; http://forums.nesdev.com/viewtopic.php?f=2&t=3958
:	bit PPUSTATUS
	bpl :-
:	bit PPUSTATUS
	bpl :-

	; Zero ram.
	txa
:	sta $000, x
	sta $100, x
	sta $200, x
	sta $300, x
	sta $400, x
	sta $500, x
	sta $600, x
	sta $700, x
	inx
	bne :-

:	bit PPUSTATUS
	bpl :-

	lda #$80
	sta PPUMASK
forever:
	jmp forever

; NMI interrupt (vertical blank).
nmi:
	rti

; IRQ interrupt.
irq:
	rti

.segment "VECTOR"
.addr nmi
.addr reset
.addr irq
