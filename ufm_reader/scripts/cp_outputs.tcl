set basename [lindex $argv 0]
file copy [file join Implementation0 ${basename}_Implementation0.bit] ${basename}.bit
file copy [file join Implementation0 ${basename}_Implementation0.jed] ${basename}.jed
