;;; ----------------------------------------------------------------------------
;;; NES addresses.

;;; PPU memory map.
PPU_NAME0	= $2000
PPU_ATTR0	= $23c0
PPU_PAL0	= $3f00

;;; PPU registers.
PPUCTRL		= $2000
PPUMASK		= $2001
PPUSTATUS	= $2002
OAMADDR		= $2003
OAMDATA		= $2004
PPUSCROLL	= $2005
PPUADDR		= $2006
PPUDATA		= $2007

;;; Other IO registers.
OAMDMA		= $4014
APUSTATUS	= $4015
JOYPAD1		= $4016
JOYPAD2		= $4017

;;; Controller buttons.
BTN_A		= $80
BTN_B		= $40
BTN_SELECT	= $20
BTN_START	= $10
BTN_UP		= $08
BTN_DOWN	= $04
BTN_LEFT	= $02
BTN_RIGHT	= $01

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
