.include "defs.s"

FLASH_TIME = 10
FLASH_COLOR1 = $20
FLASH_COLOR2 = $0f

;;; Palette adjustment.
.bss
;;; Low nybble / chroma
palcol:
	.res 1
;;; High nybble / luminance
palrow:
	.res 1
;;; Palette entry index
palidx:
	.res 1
;;; Flash counter, counts down to 0, then flash is done.
palctr:
	.res 1
;;; Original value before flash.
palsave:
	.res 1
.code

;;; Palette testing.
;;; Select/start: next/prev palette entry
;;; Up/down: increase/decrease luminance
;;; Left/right: increase/decrease chroma
.proc debug_palette
	;; Check flash.
	dec palctr
	bmi noflash
	beq flashdone
	lda #<~(BTN_A | BTN_B)
	bit buttonpress
	bne endflash
	rts

flashdone:
	;; Flash counter is done.
	lda #BTN_A
	bit buttons
	beq endflash

	;; Continue flashing while A is held down.
	ldx palidx
	lda #(FLASH_COLOR1 ^ FLASH_COLOR2)
	eor paldata, x
	sta paldata, x
	lda #FLASH_TIME
	sta palctr
	rts

endflash:
	;; Remove flash.
	ldx palidx
	lda palsave
	sta paldata, x

noflash:
	;; No flash is active.
	lda #0
	sta palctr

	;; Adjust palette index.
	lda buttonpress
	ldx #0
	asl
	asl
	asl
	bcc :+
	dex
:	asl
	bcc :+
	inx
:	txa
	beq idx_unchanged
	clc
	adc palidx
	sta palidx
	lda #$1f
	and palidx
	sta palidx
	cmp #$10
	beq do_flash
	lda #$03
	bit palidx
	bne do_flash
	txa
	clc
	adc palidx
	sta palidx
	lda #$1f
	and palidx
	sta palidx
	jmp do_flash

idx_unchanged:
	lda #BTN_A
	bit buttons
	beq dont_flash

	;; Flash the color
do_flash:
	ldx palidx
	lda #FLASH_TIME
	sta palctr
	lda paldata, x
	sta palsave
	lda #$20
	bit palsave
	beq dark
	lda #FLASH_COLOR2
	jmp setflash
dark:
	lda #FLASH_COLOR1
setflash:
	sta paldata, x
	rts

	;; Don't flash the palette entry.
dont_flash:

	;; Load the column and row.
	ldx palidx
	lda paldata, x
	sta palcol
	lsr
	lsr
	lsr
	lsr
	sta palrow

	;; Adjust column and row.
	lda buttonpress
	lsr
	bcc :+
	inc palcol
:	lsr
	bcc :+
	dec palcol
:	lsr
	bcc :+
	dec palrow
:	lsr
	bcc :+
	inc palrow
:

	;; Update the color.
	lda #$0f
	and palcol
	sta palcol
	lda palrow
	asl
	asl
	asl
	asl
	and #$30
	ora palcol
	sta paldata, x

end:
	rts
.endproc
