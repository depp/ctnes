.include "defs.s"

.zeropage
buttons:
	.res 1

.bss
nmi_done:
	.res 1

;;; ----------------------------------------------------------------------------
;;; Reset handler

.code
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
	clc
:
	tya
	asl
	asl
	tax

	asl
	and #$18
	adc #$20
	sta $0203, x		; X position

	tya
	and #$3c
	asl
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

	;; Generate background.
	clc
	setppuaddr # PPU_NAME0
	lda #0
	tay
bgrows:	ldx #0
bgrow:	sta PPUDATA
	adc #1
	inx
	cpx #32
	bne bgrow
	iny
	cpy #30
	bne bgrows

	lda #%00011011
	ldx #0
bgattr:	sta PPUDATA
	inx
	cpx #$40
	bne bgattr

	;; Final wait for PPU warmup.
:	bit PPUSTATUS
	bpl :-

	;; Enable NMI. Any other graphical setup is done by the NMI handler.
	lda #PPUCTRL_NMI
	sta PPUCTRL
mainloop:

:	bit nmi_done
	bpl :-
	lda #0
	sta nmi_done

	;; Move sprite around.
	lda buttons
	lsr
	bcc :+
	inc $0203
:	lsr
	bcc :+
	dec $0203
:	lsr
	bcc :+
	inc $0200
:	lsr
	bcc :+
	dec $0200
:

	jmp mainloop
.endproc

palette_data:
	.byte $0f,$11,$21,$31,$0f,$14,$24,$34,$0f,$17,$27,$37,$0f,$1a,$2a,$3a
	.byte $0f,$11,$21,$31,$0f,$14,$24,$34,$0f,$17,$27,$37,$0f,$1a,$2a,$3a

;;; ----------------------------------------------------------------------------
;;; NMI (vertical blank) handle

.proc nmi
	;; Load sprites.
	lda #0
	sta OAMADDR
	lda #$02
	sta OAMDMA

	;; Load palette.
	setppuaddr #$3f00
	ldx #0
:	lda palette_data, x
	sta PPUDATA
	inx
	cpx #$20
	bne :-

	;; Read the controller.
	;; https://wiki.nesdev.com/w/index.php/Controller_Reading
	;; We use the 1 to terminate the loop... once it shifts out, we end.
	lda #1
	sta JOYPAD1
	sta buttons
	lsr a
	sta JOYPAD1
:	lda JOYPAD1
	lsr a
	rol buttons
	bcc :-

	;; Set scroll.
	lda #0
	sta PPUSCROLL
	sta PPUSCROLL

	lda #PPUCTRL_NMI
	sta PPUCTRL
	lda #(PPUMASK_BG | PPUMASK_SP)
	sta PPUMASK

	lda #$80
	sta nmi_done

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
