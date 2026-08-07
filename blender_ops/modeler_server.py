"""A second, typed socket server running alongside blender-mcp's own
(port 9876), on port 9878. Where blender-mcp's execute_code hands the
model arbitrary Python, this hands it a small set of named commands built
directly on the already-verified blender_ops modules (state_probe,
persistent_ids, decision_transaction, mesh_ops) -- smaller tool outputs,
and a mutation surface that can't accidentally bypass the one-operation-
per-decision rule the way a raw exec() call always can.

This is a genuine, deliberately SMALL slice of a much larger proposed
protocol (push events, semantic regions, viewport state, ownership
locking, visual passes, ...). Rather than stub out twelve commands
untested, this wires up a complete, live-verified round trip for a few:
capability discovery, consolidated state, event polling, and the full
begin -> perform -> verify -> commit decision lifecycle for a handful of
real mesh_ops operations. Extending the operation registry in
perform_decision() is the natural next step once this slice is proven.

Threading model copied from addon.py's proven pattern: a daemon accept
thread, a daemon thread per client connection, and bpy.app.timers.register
to marshal every actual bpy/bmesh call onto Blender's main thread -- the
Python API is not safe to call from a background thread directly. Framing
is length-prefixed (4-byte big-endian uint32 + UTF-8 JSON) in both
directions, more robust than accumulate-and-retry-json.loads for a
protocol designed from scratch.
"""

import json
import os
import socket
import struct
import sys
import threading
import time
import traceback
import uuid
from collections import deque

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decision_state
import decision_transaction
import mesh_ops
import object_ops
import persistent_ids
import semantic_regions
import state_probe

PROTOCOL_VERSION = "0.1"
CAPABILITIES = [
    "selection_ids",
    "persistent_mesh_ids",
    "full_state",
    "event_polling",
    "decision_transactions",
    "external_edit_detection",
    "command_idempotency",
    "session_handshake",
    "control_mode",
    "viewport_state",
    "region_inspection",
    "semantic_regions",
]
# NOT claimed as a capability, found live during testing: an "origin" tag
# (agent vs external) was attempted on each event via a self._agent_active
# flag, on the assumption depsgraph_update_post fires within roughly one
# bpy.app.timers tick of the write that caused it. Directly instrumented
# testing disproved this -- depsgraph_update_post did not fire even 3
# seconds after a synchronous, direct mutation in this environment, only
# firing once some LATER, unrelated Blender activity (e.g. the next
# execute_blender_code call) forced a redraw/dependency-graph evaluation;
# one observed gap was over 30 seconds. The event and its timestamp are
# still real and useful for eventual "did the mesh change" polling, but
# "origin" is unreliable in the currently-shipped code and must not be
# trusted for ownership/locking decisions -- see the mesh_changed handler
# below and README for the live-tested evidence.

_OPS = {
    "bevel_edges": mesh_ops.bevel_edges,
    "merge_by_distance": mesh_ops.merge_by_distance,
    "add_ring_detail": mesh_ops.add_ring_detail,
    "recalc_normals": mesh_ops.recalc_normals,
    "triangulate_ngons": mesh_ops.triangulate_ngons,
    "extrude_selection": mesh_ops.extrude_selection,
    "move_selection": mesh_ops.move_selection,
    "scale_selection": mesh_ops.scale_selection,
    "inset_selection": mesh_ops.inset_selection,
    "add_modifier": object_ops.add_modifier,
    "set_modifier_parameter": object_ops.set_modifier_parameter,
}


class ModelerServer:
    def __init__(self, host="localhost", port=9878):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

        # Fresh per server start, not persisted to the .blend -- represents
        # THIS running server instance (directive section 14: session
        # handshake). A Blender restart means a new session_id even if the
        # same file reloads; a client can use this to detect "am I still
        # talking to the same live session I was before."
        self.session_id = uuid.uuid4().hex[:12]
        self.started_at = time.time()

        self._event_seq = 0
        self._events = deque(maxlen=500)
        self._pending = {}  # decision_id -> {"tx": DecisionTransaction, "target": str}
        self._pending_lock = threading.Lock()
        self._handlers_registered = False

        # object name -> {"verts": frozenset(ids), "edges": ..., "faces": ...}
        # as of the last point this server actually observed the mesh (a
        # begin_decision or commit_decision). Compared on the next
        # begin_decision to detect edits that happened through neither path
        # -- i.e. a human editing in the GUI. Replaces the depsgraph-timing
        # "ownership heuristic" removed above, which was disproved live: this
        # is a direct state comparison, not dependent on any event firing on
        # any particular schedule.
        self._last_known_ids = {}

        # command_id -> stored result, for perform_decision idempotency: a
        # retried call with the same command_id returns the stored result
        # instead of re-running the mutation. Unbounded for now (bounded by
        # the same guidance as _events if this becomes a real memory concern).
        self._command_journal = {}

        # Directive section 15: explicit AGENT_CONTROL / USER_CONTROL /
        # SHARED_OBSERVATION. Unlike the removed depsgraph-timing "ownership
        # heuristic" (which tried to infer origin after the fact and didn't
        # work), this is a declared mode a human or the agent sets
        # explicitly -- begin_decision enforces it directly: "never fight
        # the user's mouse" means refusing to even ATTEMPT a mutation while
        # USER_CONTROL is set, not detecting the collision after it happens.
        self._control_mode = "AGENT_CONTROL"

    # ---- lifecycle -----------------------------------------------------
    # Found live during development: importlib.reload(modeler_server) resets
    # the module-level `_server` singleton to a fresh None, but does NOT stop
    # the previous instance's still-running accept thread -- and Windows'
    # SO_REUSEADDR permits a second bind() to the same port to succeed while
    # the first socket is still listening, so hot-reloading this module
    # in-session can silently accumulate zombie listeners that intermittently
    # answer connections with stale code. Always capture and .stop() the
    # existing instance (sys.modules["modeler_server"]._server, if present)
    # before reload+start when iterating on this file live. A real Blender
    # restart does not have this problem.

    def start(self):
        if self.running:
            print("ModelerServer already running")
            return
        self.running = True
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.server_thread.start()
            self._register_event_handlers()
            print(f"ModelerServer started on {self.host}:{self.port}")
        except Exception as e:
            print(f"ModelerServer failed to start: {e}")
            self.stop()

    def stop(self):
        self.running = False
        self._unregister_event_handlers()
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        print("ModelerServer stopped")

    # ---- event stream (approximated as a pollable queue, not true push,
    # since the underlying transport is request/response) ---------------

    def _push_event(self, event_type, **data):
        # event_id is a distinct identifier from seq (directive section 7:
        # keep session_id/scene_revision/decision_id/command_id/event_id
        # separate) -- seq is purely this queue's ordering, event_id is the
        # event's own identity, stable if it were ever persisted/replayed
        # independent of queue position.
        #
        # Coalescing (directive section 9): one Blender operator can fire
        # depsgraph_update_post many times for the same object in the same
        # logical change (observed live: a single mesh edit produces
        # separate updates for the object, its mesh data, the collection,
        # and the scene). Rather than exposing each as a separate event,
        # bump a repeat count on the most recent queue entry if it already
        # represents the same (event_type, object) pair with nothing else
        # in between -- one logical entry per burst, not one per callback.
        # Verified directly (three synthetic consecutive same-object pushes
        # collapsed to one entry, repeat_count=3). Note on real-world
        # effectiveness: observed live depsgraph bursts in this environment
        # tend to ALTERNATE between the target object and a companion
        # object (e.g. object, then its mesh datablock's own name) rather
        # than repeating the same one consecutively, so this catches true
        # same-object repeats correctly but doesn't collapse an alternating
        # A/B/A/B burst -- that would need object-set-based coalescing, not
        # attempted here since the simpler form is already a real, correct
        # improvement and the alternating pattern's cause hasn't been
        # investigated.
        if self._events:
            last = self._events[-1]
            if last["event"] == event_type and last.get("object") == data.get("object"):
                last["repeat_count"] = last.get("repeat_count", 1) + 1
                last["ts"] = time.time()
                return
        self._event_seq += 1
        event_id = f"evt_{self.session_id}_{self._event_seq}"
        self._events.append({
            "event_id": event_id, "seq": self._event_seq, "ts": time.time(),
            "event": event_type, "repeat_count": 1, **data,
        })

    def _on_depsgraph_update(self, scene, depsgraph):
        for update in depsgraph.updates:
            if update.is_updated_geometry:
                self._push_event("mesh_changed", object=getattr(update.id, "name", None))

    def _on_undo_post(self, *_):
        self._push_event("undo")

    def _on_redo_post(self, *_):
        self._push_event("redo")

    def _on_save_post(self, *_):
        self._push_event("file_saved")

    def _register_event_handlers(self):
        if self._handlers_registered:
            return
        bpy.app.handlers.depsgraph_update_post.append(self._on_depsgraph_update)
        bpy.app.handlers.undo_post.append(self._on_undo_post)
        bpy.app.handlers.redo_post.append(self._on_redo_post)
        bpy.app.handlers.save_post.append(self._on_save_post)
        self._handlers_registered = True

    def _unregister_event_handlers(self):
        if not self._handlers_registered:
            return
        for handler_list, fn in (
            (bpy.app.handlers.depsgraph_update_post, self._on_depsgraph_update),
            (bpy.app.handlers.undo_post, self._on_undo_post),
            (bpy.app.handlers.redo_post, self._on_redo_post),
            (bpy.app.handlers.save_post, self._on_save_post),
        ):
            if fn in handler_list:
                handler_list.remove(fn)
        self._handlers_registered = False

    # ---- networking ------------------------------------------------------

    def _accept_loop(self):
        self.socket.settimeout(1.0)
        while self.running:
            try:
                client, addr = self.socket.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"ModelerServer accept error: {e}")
                    time.sleep(0.5)

    @staticmethod
    def _recv_exact(sock, n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf

    def _recv_message(self, sock):
        header = self._recv_exact(sock, 4)
        if header is None:
            return None
        (length,) = struct.unpack(">I", header)
        payload = self._recv_exact(sock, length)
        if payload is None:
            return None
        return json.loads(payload.decode("utf-8"))

    @staticmethod
    def _send_message(sock, obj):
        payload = json.dumps(obj).encode("utf-8")
        sock.sendall(struct.pack(">I", len(payload)) + payload)

    def _handle_client(self, client):
        client.settimeout(None)
        try:
            while self.running:
                request = self._recv_message(client)
                if request is None:
                    break

                def respond(req=request):
                    try:
                        result = self._dispatch(req.get("command"), req.get("params", {}))
                        self._send_message(client, {"id": req.get("id"), "status": "ok", "result": result})
                    except Exception as e:
                        traceback.print_exc()
                        self._send_message(client, {"id": req.get("id"), "status": "error", "message": str(e)})
                    return None

                bpy.app.timers.register(respond, first_interval=0.0)
        except Exception as e:
            print(f"ModelerServer client error: {e}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    # ---- external-edit detection (state fingerprint, not timing) --------

    @staticmethod
    def _snapshot_ids(name):
        id_maps = persistent_ids.get_id_maps(name)
        return {kind: frozenset(m["id_to_index"]) for kind, m in id_maps.items()}

    def _check_external_edit(self, name):
        """Assign IDs to any new geometry, then compare the resulting ID set
        against the last snapshot this server actually took (at the previous
        begin_decision or commit_decision). Any difference means the mesh
        changed through neither path -- an edit this server didn't perform
        and wasn't told about. Always updates the snapshot to the
        just-observed state, so a second call right after immediately sees
        no further difference (the edit has now been "seen")."""
        persistent_ids.ensure_persistent_ids(name)
        current = self._snapshot_ids(name)
        previous = self._last_known_ids.get(name)
        detected = False
        diff = {}
        if previous is not None:
            for kind in ("verts", "edges", "faces"):
                added = sorted(current[kind] - previous[kind])
                removed = sorted(previous[kind] - current[kind])
                if added or removed:
                    detected = True
                diff[kind] = {"added": added, "removed": removed}
        self._last_known_ids[name] = current
        return {"external_edit_detected": detected, "diff": diff}

    # ---- command dispatch (runs on Blender's main thread) ---------------

    def _dispatch(self, command, params):
        handler = getattr(self, f"cmd_{command}", None)
        if handler is None:
            raise ValueError(f"unknown command: {command}")
        return handler(**params)

    def cmd_get_capabilities(self):
        return {
            "protocol_version": PROTOCOL_VERSION,
            "blender_version": ".".join(str(v) for v in bpy.app.version),
            "pid": os.getpid(),
            "session_id": self.session_id,
            "started_at": self.started_at,
            "blend_filepath": bpy.data.filepath or None,
            "capabilities": CAPABILITIES,
            "available_operations": sorted(_OPS.keys()),
        }

    def cmd_heartbeat(self):
        """Cheap liveness + identity check -- a client can call this after a
        reconnect to confirm it's still talking to the same Blender process
        and server session it was before (matching pid and session_id), per
        directive section 14/16, rather than assuming a fresh connection
        means a fresh, unrelated session."""
        return {
            "session_id": self.session_id,
            "pid": os.getpid(),
            "revision": decision_state.current_revision(),
            "uptime_seconds": round(time.time() - self.started_at, 1),
            "pending_decisions": len(self._pending),
        }

    def cmd_get_full_state(self, name):
        return state_probe.get_full_state(name)

    def cmd_get_selection(self, name):
        return state_probe.get_selection(name)

    def cmd_get_viewport_state(self):
        return state_probe.viewport_state()

    def cmd_inspect_region(self, name, center_ids, rings=2):
        return state_probe.inspect_region(name, center_ids, rings=rings)

    # ---- semantic regions (named groups of persistent-ID elements) ------
    # All free to call outside a decision transaction: they store/query
    # metadata about the mesh, they don't mutate its geometry.

    def cmd_create_region(self, name, region_id, role, vertex_ids=None, edge_ids=None, face_ids=None):
        return semantic_regions.create_region(name, region_id, role, vertex_ids, edge_ids, face_ids)

    def cmd_get_region(self, name, region_id):
        return semantic_regions.get_region(name, region_id)

    def cmd_list_regions(self, name):
        return semantic_regions.list_regions(name)

    def cmd_validate_region(self, name, region_id):
        return semantic_regions.validate_region(name, region_id)

    def cmd_update_region(self, name, region_id, vertex_ids=None, edge_ids=None, face_ids=None, role=None):
        return semantic_regions.update_region(name, region_id, vertex_ids, edge_ids, face_ids, role)

    def cmd_delete_region(self, name, region_id):
        return semantic_regions.delete_region(name, region_id)

    def cmd_select_region(self, name, region_id, extend=False):
        return semantic_regions.select_region(name, region_id, extend)

    # ---- undo/redo/checkpoints (scene/file-level, not a target-object
    # decision, so not routed through perform_decision) ------------------

    def cmd_undo(self):
        return object_ops.undo()

    def cmd_redo(self):
        return object_ops.redo()

    def cmd_save_checkpoint(self, label, directory):
        return object_ops.save_checkpoint(label, directory)

    def cmd_restore_checkpoint(self, filepath):
        return object_ops.restore_checkpoint(filepath)

    def cmd_save_file(self, filepath=None):
        return object_ops.save_file(filepath)

    def cmd_select_by_ids(self, name, vertex_ids=None, edge_ids=None, face_ids=None, extend=False):
        """Selection is a mechanical helper, not a sanctioned artistic
        mutation -- free to call outside a decision transaction, matching
        mesh_ops.py's own ALLOWED/NOT-ALLOWED boundary (selection helpers are
        explicitly listed as freely callable there)."""
        return mesh_ops.select_by_ids(
            name, vertex_ids=vertex_ids, edge_ids=edge_ids, face_ids=face_ids, extend=extend
        )

    def cmd_poll_events(self, since_seq=0):
        events = [e for e in self._events if e["seq"] > since_seq]
        return {"events": events, "latest_seq": self._event_seq}

    def cmd_check_external_edit(self, name):
        """Read-only: has this object changed since the last time this
        server observed it, through a path other than a committed decision?
        Safe to poll; does not require an open transaction."""
        return self._check_external_edit(name)

    def cmd_get_control_mode(self):
        return {"control_mode": self._control_mode}

    def cmd_set_control_mode(self, mode):
        valid = {"AGENT_CONTROL", "USER_CONTROL", "SHARED_OBSERVATION"}
        if mode not in valid:
            raise ValueError(f"control_mode must be one of {sorted(valid)}, got {mode!r}")
        previous = self._control_mode
        self._control_mode = mode
        return {"previous": previous, "control_mode": mode}

    def cmd_begin_decision(self, name, action_type):
        if self._control_mode != "AGENT_CONTROL":
            raise ValueError(
                f"cannot start a decision: control_mode is '{self._control_mode}', not "
                f"'AGENT_CONTROL'. The agent does not attempt mutations while a human has "
                f"declared control -- call set_control_mode('AGENT_CONTROL') first if that's "
                f"no longer accurate."
            )
        edit_check = self._check_external_edit(name)
        if edit_check["external_edit_detected"]:
            raise ValueError(
                f"external edit detected on '{name}' since this server last observed it "
                f"(diff: {edit_check['diff']}) -- the live mesh changed outside any committed "
                f"decision, most likely a manual GUI edit. Re-observe with get_full_state before "
                f"starting a new decision; retrying begin_decision will now succeed since this "
                f"check just captured the current state as the new baseline."
            )
        obs_rev = decision_state.current_revision()
        tx = decision_transaction.decision_transaction(obs_rev, action_type, target_object=name)
        tx.__enter__()
        decision_id = f"dec_{obs_rev}_{int(time.time() * 1000)}"
        with self._pending_lock:
            self._pending[decision_id] = {"tx": tx, "target": name}
        return {"decision_id": decision_id, "observed_revision": obs_rev}

    def cmd_perform_decision(self, decision_id, operation, params, command_id=None):
        if command_id is not None and command_id in self._command_journal:
            return self._command_journal[command_id]
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id} (already committed, or begin_decision was never called)")
        fn = _OPS.get(operation)
        if fn is None:
            raise ValueError(f"unknown operation '{operation}' -- available: {sorted(_OPS.keys())}")
        result = entry["tx"].perform(fn, entry["target"], **params)
        response = {"decision_id": decision_id, "performed": True, "result": result}
        if command_id is not None:
            self._command_journal[command_id] = response
        return response

    def cmd_verify_decision(self, decision_id):
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id}")
        return entry["tx"].verify()

    def cmd_commit_decision(self, decision_id):
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id}")
        new_rev = entry["tx"].commit()
        target = entry["target"]
        with self._pending_lock:
            del self._pending[decision_id]
        self._check_external_edit(target)  # refresh the snapshot to this decision's own result
        return {"decision_id": decision_id, "result_revision": new_rev}


_server = None


def get_server():
    global _server
    if _server is None:
        _server = ModelerServer()
    return _server


def start():
    get_server().start()


def stop():
    global _server
    if _server is not None:
        _server.stop()
