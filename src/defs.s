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

;;; PPUCTRL flags.
PPUCTRL_NAMEX	= $01		; Nametable X=1.
PPUCTRL_NAMEY	= $02		; Nametable Y=1.
PPUCTRL_VWRITE	= $04		; Write PPUDATA vertically (32 byte stride).
PPUCTRL_SPRPAT	= $08		; Sprite pattern table 1.
PPUCTRL_BGPAT	= $10		; Background pattern table 1.
PPUCTRL_SPRSZ	= $20		; 8x16 sprites.
PPUCTRL_NMI	= $80		; Enable NMI.

;;; PPUMASK flags.
PPUMASK_GRAY	= $01		; Grayscale output.
PPUMASK_BGLEFT	= $02		; Enable left 8 columns of background.
PPUMASK_SPLEFT	= $04		; Enable left 8 columns of sprites.
PPUMASK_BG	= $08		; Enable background.
PPUMASK_SP	= $10		; Enable sprites.
PPUMASK_RED	= $20		; Emphasize red (green on PAL, Dendy).
PPUMASK_GREEN	= $40		; Emphasize green (red on PAL, Dendy).
PPUMASK_BLUE	= $80		; Emphasize blue.

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

;;; setppuaddr sets the PPU address for writes.
;;; clobbered: A
.macro setppuaddr addr
	.if .paramcount <> 1
	.error "Expect exactly one argument"
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

;;; ----------------------------------------------------------------------------
;;; RAM

;;; 256-byte buffer where we store OAM data for the next frame.
oam_buffer = $0200

;;; Palette to be uploaded.
.global paldata

;;; Controller state.
.globalzp buttons, buttonpress

;;; Parameters for emit_sprite.
.globalzp sprite_x, sprite_y, sprite_index
;;; Write a sprite to the sprite buffer.
.global emit_sprite

;;; The level data, as a raw PPU name table.
.import leveldata

;;; Debugging
.global debug_palette
