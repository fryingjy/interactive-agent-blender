"""A second, typed socket server running alongside blender-mcp's own
(port 9876), on port 9878. Where blender-mcp's execute_code hands the
model arbitrary Python, this hands it a small set of named commands built
directly on the already-verified blender_ops modules (state_probe,
persistent_ids, decision_transaction, mesh_ops) -- smaller tool outputs,
and a mutation surface that can't accidentally bypass the one-operation-
per-decision rule the way a raw exec() call always can.

The protocol began as a deliberately small live-verified slice. It now includes capability/state
inspection, events, semantic regions, visual/evaluated evidence, and an expanded typed mutation
surface routed through the same begin -> perform -> verify -> commit/reject lifecycle.

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
import curve_ops
import decision_state
import decision_transaction
import evaluated_probe
import mesh_ops
import modeling_stage
import object_ops
import persistent_ids
import render_passes
import semantic_regions
import state_fingerprint
import state_probe

PROTOCOL_VERSION = "0.3"
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
    "evaluated_mesh_inspection",
    "decision_rollback",
    "layered_state_fingerprint",
    "native_silhouette_render",
    "curve_bevel_taper_geometry",
    "modeling_stage_tracking",
    "expanded_typed_modeling_surface",
    "diagnostic_visual_passes",
    "surface_candidate_diagnostics",
    "bridge_correspondence_analysis",
    "editable_high_low_variant_packaging",
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
    "subdivide_selection": mesh_ops.subdivide_selection,
    "rotate_selection": mesh_ops.rotate_selection,
    "bevel_selection": mesh_ops.bevel_selection,
    "delete_selection": mesh_ops.delete_selection,
    "dissolve_selection": mesh_ops.dissolve_selection,
    "merge_selection": mesh_ops.merge_selection,
    "fill_selection": mesh_ops.fill_selection,
    "bridge_selection": mesh_ops.bridge_selection,
    "spin_selection": mesh_ops.spin_selection,
    "loop_cut_selection": mesh_ops.loop_cut_selection,
    "bisect_selection": mesh_ops.bisect_selection,
    "symmetrize_selection": mesh_ops.symmetrize_selection,
    "split_selection": mesh_ops.split_selection,
    "separate_selection": mesh_ops.separate_selection,
    "assign_vertex_group": mesh_ops.assign_vertex_group,
    "add_modifier": object_ops.add_modifier,
    "set_modifier_parameter": object_ops.set_modifier_parameter,
    "package_high_low_variants": object_ops.package_high_low_variants,
    "set_shading": object_ops.set_shading,
    "set_smooth_by_angle": object_ops.set_smooth_by_angle,
    "set_bevel_weight_by_ids": object_ops.set_bevel_weight_by_ids,
    "set_bevel_scoping": object_ops.set_bevel_scoping,
    "set_edge_crease_by_ids": object_ops.set_edge_crease_by_ids,
    "mark_no_sharp_edges_needed": object_ops.mark_no_sharp_edges_needed,
}


class ModelerServer:
    def __init__(self, host="localhost", port=9878):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

        # Fresh per server start, not persisted to the .blend -- represents
        # THIS running server instance (master directive section 9: state
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

        # object name -> state_fingerprint.compute() result, as of the last
        # point this server actually observed the mesh (a begin_decision or
        # commit_decision/reject_decision). Compared on the next
        # begin_decision to detect edits that happened through neither path
        # -- i.e. a human editing in the GUI. Replaces the depsgraph-timing
        # "ownership heuristic" removed above, which was disproved live: this
        # is a direct state comparison, not dependent on any event firing on
        # any particular schedule. Originally only compared persistent-ID
        # SETS (topology add/remove); extended (directive P0.2) to also
        # catch existing-vertex movement, object transform changes, and
        # modifier parameter changes that leave every ID untouched -- see
        # state_fingerprint.py.
        self._last_known_fingerprint = {}

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
        # event_id is a distinct identifier from seq (master directive section 9:
        # keep session_id/scene_revision/decision_id/command_id/event_id
        # separate) -- seq is purely this queue's ordering, event_id is the
        # event's own identity, stable if it were ever persisted/replayed
        # independent of queue position.
        #
        # Coalescing: one Blender operator can fire
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

    def _check_external_edit(self, name):
        """Assign IDs to any new geometry, then compare a full layered
        fingerprint (topology + geometry hash + transform + modifier params)
        against the last one this server actually took (at the previous
        begin_decision or commit_decision/reject_decision). Any layer
        differing means the object changed through neither path -- an edit
        this server didn't perform and wasn't told about. Always updates the
        snapshot to the just-observed state, so a second call right after
        immediately sees no further difference (the edit has now been
        "seen")."""
        persistent_ids.ensure_persistent_ids(name)
        current = state_fingerprint.compute(name)
        previous = self._last_known_fingerprint.get(name)
        detected = False
        diff = {}
        if previous is not None:
            detected, diff = state_fingerprint.diff(previous, current)
        self._last_known_fingerprint[name] = current
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
        master directive sections 3 and 9, rather than assuming a fresh connection
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

    def cmd_create_primitive(self, name, primitive_type, location=None, **kwargs):
        """The one-time starting block a modeling session begins from --
        free to call outside a decision transaction (nothing exists yet
        for begin_decision's external-edit check to compare against)."""
        loc = tuple(location) if location else (0.0, 0.0, 0.0)
        return object_ops.create_primitive(name, primitive_type, location=loc, **kwargs)

    def cmd_create_curve(self, name, points, bevel_depth=0.05, closed=False, curve_type="POLY"):
        """Free to call outside a decision transaction, same reasoning as
        create_primitive -- a new curve object, nothing yet exists for
        begin_decision's external-edit check to compare against."""
        return curve_ops.create_curve_from_points(name, points, bevel_depth=bevel_depth, closed=closed, curve_type=curve_type)

    def cmd_set_curve_bevel_depth(self, name, depth):
        return curve_ops.set_curve_bevel_depth(name, depth)

    def cmd_set_curve_taper(self, name, taper_object_name):
        return curve_ops.set_curve_taper(name, taper_object_name)

    def cmd_convert_curve_to_mesh(self, name, new_mesh_name=None, merge_dist=0.0001):
        return curve_ops.convert_curve_to_mesh(name, new_mesh_name=new_mesh_name, merge_dist=merge_dist)

    def cmd_get_modeling_stage(self, name):
        return {"name": name, "stage": modeling_stage.get_stage(name), "log": modeling_stage.get_stage_log(name)}

    def cmd_set_modeling_stage(self, name, stage, evidence):
        if stage not in modeling_stage.STAGES:
            raise ValueError(f"stage must be one of {modeling_stage.STAGES}")
        current = modeling_stage.get_stage(name)
        if current not in modeling_stage.STAGES:
            raise ValueError(f"object {name!r} has invalid persisted modeling stage: {current!r}")
        if modeling_stage.STAGES.index(stage) < modeling_stage.STAGES.index(current):
            return modeling_stage.set_stage(name, stage, evidence)
        return modeling_stage.advance_stage(name, stage, evidence)

    def cmd_get_selection(self, name):
        return state_probe.get_selection(name)

    def cmd_list_persistent_ids(self, name):
        return state_probe.list_persistent_ids(name)

    def cmd_get_viewport_state(self):
        return state_probe.viewport_state()

    def cmd_get_evaluated_state(self, name):
        return {
            "mesh_health": evaluated_probe.evaluated_mesh_health(name),
            "valence_distribution": evaluated_probe.evaluated_valence_distribution(name),
            "surface_quality": evaluated_probe.evaluated_surface_quality(name),
            "surface_diagnostics": evaluated_probe.evaluated_surface_diagnostics(name),
            "bounding_box": evaluated_probe.bounding_box_comparison(name),
        }

    def cmd_analyze_bridge_selection(self, name, twist_offsets=None, allow_unequal=False):
        """Read-only simulation of candidate Bridge Edge Loops correspondences."""
        return mesh_ops.analyze_bridge_selection(
            name,
            twist_offsets=twist_offsets,
            allow_unequal=allow_unequal,
        )

    def cmd_get_hard_surface_shading_audit(self, name):
        return object_ops.hard_surface_shading_audit(name)

    def cmd_get_evaluated_defect_regions(self, name, area_outlier_ratio=0.05, angle_threshold_degrees=10, angle_local_spike_ratio=2.0, max_tickets=20):
        return evaluated_probe.evaluated_defect_regions(
            name, area_outlier_ratio=area_outlier_ratio,
            angle_threshold_degrees=angle_threshold_degrees,
            angle_local_spike_ratio=angle_local_spike_ratio, max_tickets=max_tickets)

    def cmd_inspect_region(self, name, center_ids, rings=2):
        return state_probe.inspect_region(name, center_ids, rings=rings)

    def cmd_render_silhouette(self, name, output_path, view="front", resolution=512, margin=1.15):
        """Free to call outside a decision transaction -- a render is a
        read of the current state, not a mutation, same as get_full_state."""
        return render_passes.render_silhouette(name, output_path, view=view, resolution=resolution, margin=margin)

    def cmd_render_diagnostic_pass(self, name, output_path, pass_type, view="front", resolution=512, margin=1.15, frame_name=None):
        return render_passes.render_diagnostic_pass(
            name, output_path, pass_type, view=view, resolution=resolution,
            margin=margin, frame_name=frame_name)

    def cmd_render_semantic_region(self, name, region_id, output_path, view="front", resolution=512, margin=1.15):
        return render_passes.render_semantic_region(
            name, region_id, output_path, view=view, resolution=resolution, margin=margin)

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
            # _check_external_edit just above set self._last_known_fingerprint[name]
            # to the state observed at THIS moment -- capture it as this
            # transaction's own baseline, so perform_decision can re-verify
            # nothing changed between begin and perform (see the correction
            # in cmd_perform_decision for why this matters).
            self._pending[decision_id] = {
                "tx": tx, "target": name,
                "baseline_fingerprint": self._last_known_fingerprint.get(name),
            }
        return {"decision_id": decision_id, "observed_revision": obs_rev}

    def cmd_perform_decision(self, decision_id, operation, params, command_id=None):
        if command_id is not None and command_id in self._command_journal:
            return self._command_journal[command_id]
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id} (already committed, or begin_decision was never called)")
        # CORRECTION (found live, testing the mid-transaction-edit scenario
        # covered by master directive section 9): begin_decision only proves the
        # mesh was clean AT THAT MOMENT. Nothing previously re-checked
        # before the actual mutation ran -- a human edit landing between
        # begin_decision and perform_decision was silently absorbed with
        # zero indication anything unexpected happened, confirmed directly
        # (moved a vertex mid-transaction, perform_decision succeeded
        # without complaint, verify_decision's before/after showed nothing
        # wrong since vertex COUNT hadn't changed, only a position). Not
        # auto-refreshing the baseline here the way begin_decision's own
        # check does on failure -- that would silently fold the human's
        # edit into what the agent then treats as its own starting point,
        # exactly what master directive sections 9 and 16 prohibit (human
        # corrections are evidence to reason about, not something to
        # silently absorb without surfacing).
        baseline_fp = entry.get("baseline_fingerprint")
        if baseline_fp is not None:
            current_fp = state_fingerprint.compute(entry["target"])
            detected, diff = state_fingerprint.diff(baseline_fp, current_fp)
            if detected:
                raise ValueError(
                    f"external edit detected on '{entry['target']}' since this decision began "
                    f"(diff: {diff}) -- the mesh changed mid-transaction, most likely a manual "
                    f"GUI edit. This transaction is now stale: call reject_decision to discard "
                    f"it, then begin_decision again to re-observe the current state."
                )
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

    def cmd_abandon_decision(self, decision_id, reason=""):
        """Discard a pending decision that never reached perform() -- e.g.
        begin_decision succeeded but perform_decision then failed (a
        mid-transaction external edit, an invalid operation name, bad
        params). reject_decision correctly refuses this case (there is no
        mutation to roll back), which otherwise leaves the entry in
        self._pending forever with no way to clear it except a full server
        restart -- found live immediately after adding the mid-transaction
        edit check above, which is exactly the situation that produces a
        never-performed pending decision in normal use, not an edge case."""
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id}")
        if entry["tx"]._performed:
            raise ValueError(
                f"decision {decision_id} already has a performed mutation -- use "
                f"reject_decision (to roll it back) or commit_decision, not abandon_decision"
            )
        with self._pending_lock:
            del self._pending[decision_id]
        return {
            "decision_id": decision_id,
            "abandoned": True,
            "reason": reason,
            "failed_operation_rolled_back": entry["tx"]._failure_rolled_back,
        }

    def cmd_reject_decision(self, decision_id, reason=""):
        """Transaction-owned rollback (directive P0.1): restore the target
        object to exactly its pre-perform() state, independent of Blender's
        global undo stack. decision_state's revision counter is left
        untouched (never advanced), so the scene is exactly as if this
        decision never happened -- the caller does not need to re-observe a
        "new" revision afterward, observed_revision is still current."""
        entry = self._pending.get(decision_id)
        if entry is None:
            raise ValueError(f"no pending decision {decision_id}")
        result = entry["tx"].reject(reason=reason)
        target = entry["target"]
        with self._pending_lock:
            del self._pending[decision_id]
        self._check_external_edit(target)  # refresh the snapshot to the restored (reverted) state
        return {"decision_id": decision_id, **result}


_server = None


def get_server():
    global _server
    if _server is None:
        _server = ModelerServer()
    return _server


def start():
    get_server().start()


def stop():
    if _server is not None:
        _server.stop()
