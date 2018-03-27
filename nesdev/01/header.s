;;; ----------------------------------------------------------------------------
;;; iNES ROM image header

;;; Size of PRG in units of 16 KiB.
prg_npage = 1
;;; Size of CHR in units of 8 KiB.
chr_npage = 1
;;; INES mapper number.
mapper = 0
;;; Mirroring (0 = horizontal, 1 = vertical)
mirroring = 1

.segment "INES"
	.byte $4e, $45, $53, $1a
	.byte prg_npage
	.byte chr_npage
	.byte ((mapper & $0f) << 4) | (mirroring & 1)
	.byte mapper & $f0
