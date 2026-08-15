# Failed first Blender attempt

The first factory-startup run stopped before any artistic mutation with `KeyError: 10` while resolving the two cap-face IDs. The script had assumed `get_full_state()` assigns missing persistent IDs; it only reports coverage. The correction uses `cmd_check_external_edit()` as the server-owned read-only handshake that both ensures IDs and captures the initial state baseline. The complete traceback remains in the task terminal history; this note prevents the failed attempt from disappearing from the committed experiment record.
