# Typed sequence fail-closed control

This negative control sends a render command an absent object. The typed command returns an error dictionary; the sequence runner must convert that into a failed step, nonzero process exit, and `pass: false` report instead of silently recording `status: ok`.
