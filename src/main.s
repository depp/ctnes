.include "defs.s"

;;; ----------------------------------------------------------------------------
;;; Reset handler

.proc reset
	sei
	cld
	ldx #$ff
	txs
	inx
	stx PPUCTRL
	stx PPUMASK
	stx APUSTATUS

	;; PPU warmup, wait two frames, plus a third later.
	;; http://forums.nesdev.com/viewtopic.php?f=2&t=3958
:	bit PPUSTATUS
	bpl :-
:	bit PPUSTATUS
	bpl :-

	;; Zero ram.
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

	;; Generate sprites.
	ldy #$0
:
	tya
	asl
	asl
	tax

	asl
	and #$38
	adc #$20
	sta $0203, x		; X position

	tya
	and #$38
	adc #$20
	sta $0200, x		; Y position

	tya
	and #$03
	sta $0202, x		; Palette

	iny
	tya
	sta $0201, x		; Tile
	cpy #$40

	bne :-

	;; Final wait for PPU warmup.
:	bit PPUSTATUS
	bpl :-

	lda #%10000000
	sta PPUCTRL
	lda #%00010000
	sta PPUMASK
forever:
	jmp forever
.endproc

palette_data:
	.byte $0f,$11,$21,$31,$0f,$14,$24,$34,$0f,$17,$27,$37,$0f,$1a,$2a,$3a
	.byte $0f,$11,$21,$31,$0f,$14,$24,$34,$0f,$17,$27,$37,$0f,$1a,$2a,$3a

object_data:
	.byte $80,$01,$00,$80
	.byte $80,$02,$01,$90
	.byte $80,$03,$02,$a0
	.byte $80,$04,$03,$b0

;;; ----------------------------------------------------------------------------
;;; NMI (vertical blank) handle

.proc nmi
	;; load palette
	setppuaddr #($3f00 + $10)
	ldx #0
:	lda palette_data, x
	sta PPUDATA
	inx
	cpx #$20
	bne :-

	;; load sprites
	lda #0
	sta OAMADDR
	lda #$02
	sta OAMDMA

	rti
.endproc

;;; ----------------------------------------------------------------------------
;;; IRQ handler

.proc irq
	rti
.endproc

;;; ----------------------------------------------------------------------------
;;; Vector table

.segment "VECTOR"
.addr nmi
.addr reset
.addr irq
