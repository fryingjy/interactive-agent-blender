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
from collections import deque

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decision_state
import decision_transaction
import mesh_ops
import persistent_ids
import state_probe

PROTOCOL_VERSION = "0.1"
CAPABILITIES = [
    "selection_ids",
    "persistent_mesh_ids",
    "full_state",
    "event_polling",
    "decision_transactions",
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
}


class ModelerServer:
    def __init__(self, host="localhost", port=9878):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

        self._event_seq = 0
        self._events = deque(maxlen=500)
        self._pending = {}  # decision_id -> {"tx": DecisionTransaction, "target": str}
        self._pending_lock = threading.Lock()
        self._handlers_registered = False

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
        self._event_seq += 1
        self._events.append({"seq": self._event_seq, "ts": time.time(), "event": event_type, **data})

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
            "capabilities": CAPABILITIES,
            "available_operations": sorted(_OPS.keys()),
        }

    def cmd_get_full_state(self, name):
        return state_probe.get_full_state(name)

    def cmd_get_selection(self, name):
        return state_probe.get_selection(name)

    def cmd_poll_events(self, since_seq=0):
        events = [e for e in self._events if e["seq"] > since_seq]
        return {"events": events, "latest_seq": self._event_seq}

    def cmd_begin_decision(self, name, action_type):
        obs_rev = decision_state.current_revision()
        tx = decision_transaction.decision_transaction(obs_rev, action_type, target_object=name)
        tx.__enter__()
        decision_id = f"dec_{obs_rev}_{int(time.time() * 1000)}"
        with self._pending_lock:
            self._pending[decision_id] = {"tx": tx, "target": name}
        return {"decision_id": decision_id, "observed_revision": obs_rev}

    def cmd_perform_decision(self, decision_id, operation, params):
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id} (already committed, or begin_decision was never called)")
        fn = _OPS.get(operation)
        if fn is None:
            raise ValueError(f"unknown operation '{operation}' -- available: {sorted(_OPS.keys())}")
        result = entry["tx"].perform(fn, entry["target"], **params)
        return {"decision_id": decision_id, "performed": True, "result": result}

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
        with self._pending_lock:
            del self._pending[decision_id]
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
