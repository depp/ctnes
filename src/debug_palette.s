.include "defs.s"

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

.code

;;; Palette testing.
;;; Select/start: next/prev palette entry
;;; Up/down: increase/decrease luminance
;;; Left/right: increase/decrease chroma
.proc debug_palette
	;; Adjust palette index.
	lda buttonpress
	asl
	asl
	ldx #0
	asl
	bcc :+
	dec palidx
:	asl
	bcc :+
	inc palidx
:

	lda #$1f
	and palidx
	sta palidx
	tax
	lda paldata, x
	sta palcol
	lsr
	lsr
	lsr
	lsr
	sta palrow

	;; Adjust palette color.
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

	rts
.endproc
