.segment "INES"
.byte "NES", $1A
.byte 1		; Size of PRG in units of 16 KiB.
.byte 0		; Size of CHR in units of 8 KiB.
.byte 1		; Flags, vertical mirroring.

.code

; NMI interrupt.
nmi:
	rti

; NES demo,
; http://wiki.nesdev.com/w/index.php/Programming_Basics
reset:
	lda #$01
	sta $4015
	lda #$08
	sta $4002
	lda #$02
	sta $4003
	lda #$bf
	sta $400
forever:
	jmp forever

; IRQ interrupt.
irq:
	rti

.segment "VECTOR"
.addr nmi
.addr reset
.addr irq
