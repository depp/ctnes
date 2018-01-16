.include "defs.s"

.include "spritedata.s"

.zeropage
sprite_x:
	.res 1
sprite_y:
	.res 1
sprite_index:
	.res 1

.code
.proc emit_sprite
	ldy sprite_index
	lda sprites + 1, y	; reuse sprite_index = last part index
	sta sprite_index
	ldx sprites, y		; X = part index
	ldy #0			; Y = output OAM offset
loop:
	lda yoffsets, x
	clc
	adc sprite_y
	sta oam_buffer, y	; Y position
	iny
	lda indexes, x
	sta oam_buffer, y	; Tile index
	iny
	lda palettes, x
	sta oam_buffer, y	; Attributes
	iny
	lda xoffsets, x
	clc
	adc sprite_x
	sta oam_buffer, y	; X position
	iny
	inx
	cpx sprite_index	; compare X == last part index
	bne loop
	rts
.endproc
