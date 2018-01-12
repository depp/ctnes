; PPU memory map.
PPU_NAME0	= $2000
PPU_ATTR0	= $23c0
PPU_PAL0	= $3f00

; PPU registers.
PPUCTRL		= $2000
PPUMASK		= $2001
PPUSTATUS	= $2002
OAMADDR		= $2003
OAMDATA		= $2004
PPUSCROLL	= $2005
PPUADDR		= $2006
PPUDATA		= $2007

OAMDMA		= $4014
APUSTATUS	= $4015

.include "charmap.s"

;;; setppuaddr sets the PPU address for writes.
;;; clobbered: A
.macro setppuaddr addr
	.if .paramcount <> 1
	.error "neext exactly one argument"
	.endif

	lda PPUSTATUS		; Reset latch

	.if .match(.left(1, {addr}), #)
	lda #.hibyte(.right(.tcount({addr})-1, {addr}))
	sta PPUADDR
	lda #.lobyte(.right(.tcount({addr})-1, {addr}))
	sta PPUADDR

	.else
	.error "Bad PPU address"
	.endif
.endmacro
