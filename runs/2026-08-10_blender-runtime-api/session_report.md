# Blender runtime API lifecycle

**Date:** 2026-08-10  
**Blender:** 5.2.0 LTS  
**Status:** PASS for scoped lifecycle contracts; asynchronous delivery not claimed

## Result

Six assertions cover `bpy.context` versus `bpy.data` object authority, Mesh/Object/Modifier RNA
types, dependency-graph evaluation, handler registration/callback/removal, timer
registration/removal, and message-bus subscription/publish/owner cleanup. A Bevel evaluated from 8
base vertices to 56 without mutating the base mesh. The saved evaluated result independently
verifies clean.

## Preserved failures and boundaries

- `bpy.msgbus.subscribe_rna` rejected `list.append` because `notify` requires a Python function;
  an explicit wrapper fixed the contract.
- Explicit message-bus publish queued no callback while the background script monopolized
  execution. Timer execution was similarly not yielded. The final pass proves registration,
  publication calls, and cleanup but explicitly does not claim asynchronous event-loop delivery.
- The depsgraph handler callback is invoked directly with the real scene/depsgraph to verify its
  signature and lifecycle. Automatic event dispatch is not claimed by this blocking fixture.

Production server behavior that depends on timers or notifications must therefore be tested in a
persistent GUI/event-loop session, not inferred from this background lifecycle test.
