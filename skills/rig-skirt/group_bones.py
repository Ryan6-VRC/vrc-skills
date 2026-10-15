"""Grouping pass for rig-skirt §Grouping: add one unweighted top bone per group and reparent the group's members under it.

    blender -b --factory-startup --python group_bones.py -- --in <in.blend> --group NAME=B1,B2[,...] [--group ...]
        [--armature OBJ] [--max-spread DEG] (--whatif | --out <out.blend>)

Each group bone is parented where its members were (they must share one parent), takes its head at the mean of the members' heads, its length
at their mean length, and its frame from the normalised quaternion mean of their rest rotations; a one-member group doubles that bone's top
with the member's own frame. The bone does not deform. Run it on the blend the costume's record names as the rig's authority (an unreduced
blend, where the record keeps one), never on a derived one, then follow the record's re-export chain.

Refuses, writing nothing: an armature or its data linked from a library; a group name that is already a bone; a member that is missing, in two
groups, or not sharing its group's parent; a bone constraint on a member or any bone below one, since reparenting changes the space it
evaluates in; a mesh vertex group named for a group bone; and a mean frame more than --max-spread degrees (default 60) from any member's,
which is what a mirror-rolled pair yields (two frames near 180 degrees apart average to a frame that matches neither, and the group top's
constraint offsets then read the frame trap rig-skirt §Deriving the table names); unify the rolls or group the pair apart.

Before saving it asserts that no existing bone moved (rotation 1e-3 degrees, head and tail 1e-6 m), every member has its planned parent, and
every group bone landed on its planned frame. X-mirror editing is held off for the edit, since it would rewrite each mirror twin as its
partner is framed, and restored after.

Prints PATH lines, every bone whose hierarchy path changes (members and everything below them), old and new: the pre-export inventory. An FBX
reparent re-mints those bones' Unity fileIDs and drops every prefab-variant component on them (docs/unity.md §Geometry-change reconcile), so
list the components on exactly these paths before the re-export. GROUP lines give each group's head, azimuth (armature space read as Unity
avatar space: 0 front, negative the avatar's left, -Y taken as forward), length, frame error and each member's angle to the new frame.

--whatif runs every step and assert and saves nothing. A real run saves to --out (never --in) with relative paths remapped and the input's
compression. Exit 0 on => OK, 1 on => FAIL (a refusal or a failed assert), 2 on bad arguments or a file that will not open cleanly."""
import sys, os, math, argparse

TOOL = 'group_bones'


def out(msg):
    print('%s: %s' % (TOOL, msg))


def fail(msg, code=1):
    out('=> FAIL: ' + msg)
    sys.exit(code)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail('bad args: ' + message, 2)


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = _Parser(prog=TOOL)
    p.add_argument('--in', dest='in_path', required=True)
    p.add_argument('--group', action='append', required=True, metavar='NAME=B1,B2')
    p.add_argument('--armature', default=None, help='armature object; default the only local one')
    p.add_argument('--max-spread', type=float, default=60.0, help='largest member-to-mean frame angle, degrees')
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--whatif', action='store_true')
    mode.add_argument('--out', dest='out_path')
    a = p.parse_args(argv)
    groups = {}
    for spec in a.group:
        name, sep, members = spec.partition('=')
        name = name.strip(); mem = [m.strip() for m in members.split(',') if m.strip()]
        if not sep or not name or not mem: fail('--group %r: want NAME=B1,B2' % spec, 2)
        if name in groups: fail('--group %s given twice' % name, 2)
        if len(set(mem)) != len(mem): fail('--group %s names a member twice' % name, 2)
        groups[name] = mem
    if a.out_path and os.path.abspath(a.out_path) == os.path.abspath(a.in_path):
        fail('--out is --in; write beside the input so it stays the rollback', 2)
    return a, groups


def open_input(path, writes):
    import bpy
    req = os.path.abspath(path)
    if not os.path.isfile(req): fail('no such file: ' + req, 2)
    try:
        bpy.ops.wm.open_mainfile(filepath=req)
    except RuntimeError as e:
        # Blender raises on a file it loaded with repairs; saving would persist them
        if writes: fail('open reported %s; a write would persist the repair: inspect and re-save the source first' % e, 2)
        out('open reported %s; reading only' % e)
    if not bpy.data.filepath or not os.path.samefile(bpy.data.filepath, req): fail('did not open ' + req, 2)
    missing = [l.filepath for l in bpy.data.libraries if l.filepath and not os.path.exists(bpy.path.abspath(l.filepath))]
    if missing and writes: fail('linked libraries do not resolve %s; a save would write placeholders' % missing, 2)


def qmean(qs):
    from mathutils import Quaternion
    ref = qs[0]; acc = Quaternion((0, 0, 0, 0))
    for q in qs:
        q = q.copy()
        if ref.dot(q) < 0: q.negate()
        acc = Quaternion([x + y for x, y in zip(acc, q)])
    norm = acc.magnitude / len(qs)
    acc.normalize()
    return acc, norm


def ang(a, b):
    x = math.degrees(a.rotation_difference(b).angle)
    return min(x, 360 - x)


def path_of(bone):
    parts = []
    while bone is not None: parts.append(bone.name); bone = bone.parent
    return '/'.join(reversed(parts))


def main():
    import bpy
    from mathutils import Vector
    a, GROUPS = parse_args()
    open_input(a.in_path, writes=not a.whatif)

    if a.armature:
        arm = bpy.data.objects.get(a.armature)
        if arm is None or arm.type != 'ARMATURE': fail('--armature %s is not an armature object' % a.armature, 2)
    else:
        arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.library is None]
        if len(arms) != 1: fail('%d local armatures %s; pass --armature' % (len(arms), [o.name for o in arms]), 2)
        arm = arms[0]
    if arm.library is not None or arm.data.library is not None or arm.override_library is not None:
        fail('%s is linked or overridden; group on the blend that owns it' % arm.name)
    bones = arm.data.bones

    # refusals before any edit
    owner = {}
    for g, mem in GROUPS.items():
        if g in bones: fail('group bone %s already exists; this pass runs on an ungrouped rig' % g)
        for m in mem:
            if m not in bones: fail('group %s: no bone %s' % (g, m))
            if m in owner: fail('bone %s is in groups %s and %s' % (m, owner[m], g))
            owner[m] = g
        parents = {bones[m].parent.name if bones[m].parent else None for m in mem}
        if len(parents) != 1 or None in parents:
            fail('group %s: members must share one parent bone, have %s' % (g, sorted(str(p) for p in parents)))
    constrained = []
    for m in owner:
        for b in [bones[m]] + list(bones[m].children_recursive):
            pb = arm.pose.bones[b.name]
            if len(pb.constraints): constrained.append('%s (%s)' % (b.name, ', '.join(c.type for c in pb.constraints)))
    if constrained: fail('bone constraints on members or below would re-evaluate in a new parent space: %s; remove or re-target them first' % constrained)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.library is None:
            clash = [vg.name for vg in o.vertex_groups if vg.name in GROUPS]
            if clash: fail('mesh %s already has vertex groups %s; a group bone of that name would skin it' % (o.name, clash))

    before = {b.name: (b.matrix_local.copy(), b.head_local.copy(), b.tail_local.copy(), b.parent.name if b.parent else None) for b in bones}
    restq = {n: v[0].to_quaternion() for n, v in before.items()}
    old_paths = {b.name: path_of(b) for b in bones}

    plan = {}
    for g, mem in GROUPS.items():
        q, norm = qmean([restq[m] for m in mem])
        spread = max(ang(restq[m], q) for m in mem)
        if spread > a.max_spread or norm < 1e-3:
            fail('group %s: mean frame sits %.1f deg from a member (bar %.0f); a mirror-rolled pair averages to a frame matching neither: '
                 'unify the rolls in Blender or group them apart' % (g, spread, a.max_spread))
        head = sum((bones[m].head_local for m in mem), Vector()) / len(mem)
        length = sum(bones[m].length for m in mem) / len(mem)
        plan[g] = (head, q, length, bones[mem[0]].parent.name)

    for o in bpy.context.view_layer.objects: o.select_set(o == arm)
    bpy.context.view_layer.objects.active = arm
    mirror = arm.data.use_mirror_x; arm.data.use_mirror_x = False
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        eb = arm.data.edit_bones
        for g in GROUPS: eb.new(g)                  # create every bone first: EditBone handles go stale across new()
        for g in GROUPS:
            head, q, length, parent = plan[g]; R = q.to_matrix()
            nb = eb[g]
            # a fresh zero-length bone ignores EditBone.matrix: set head and tail, then roll, then assert the frame
            nb.head = head; nb.tail = head + R.col[1] * length; nb.align_roll(R.col[2])
            nb.parent = eb[parent]; nb.use_connect = False; nb.use_deform = False
        for g, mem in GROUPS.items():
            for m in mem: eb[m].use_connect = False; eb[m].parent = eb[g]
        for g in GROUPS:
            e = ang(eb[g].matrix.to_quaternion(), plan[g][1])
            if e > 1e-3: fail('edit frame of %s is %.5f deg off plan' % (g, e))
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        arm.data.use_mirror_x = mirror

    bad = []; worst = [0.0, 0.0, 0.0]
    for n, (M, h, t, par) in before.items():
        b = bones[n]
        dr = ang(b.matrix_local.to_quaternion(), M.to_quaternion()); dh = (b.head_local - h).length; dt = (b.tail_local - t).length
        worst = [max(worst[0], dr), max(worst[1], dh), max(worst[2], dt)]
        if dr > 1e-3 or dh > 1e-6 or dt > 1e-6: bad.append('%s moved (%.4f deg, %.2g m, %.2g m)' % (n, dr, dh, dt))
        want = owner.get(n, par)
        got = b.parent.name if b.parent else None
        if got != want: bad.append('%s parent %s, planned %s' % (n, got, want))
    for g in GROUPS:
        e = ang(bones[g].matrix_local.to_quaternion(), plan[g][1])
        if e > 1e-3: bad.append('object frame of %s is %.5f deg off plan' % (g, e))
    if bad: fail('DRIFT %s' % bad[:10])
    out('DRIFT_ASSERT ok: %d existing bones; worst rotation %.6f deg, head %.3g m, tail %.3g m; parents as planned' % (len(before), *worst))

    changed = [(old_paths[n], path_of(bones[n])) for n in old_paths if path_of(bones[n]) != old_paths[n]]
    for o, n in sorted(changed): out('PATH %s -> %s' % (o, n))
    out('PATHS %d bones change path; list the prefab components on them before the re-export' % len(changed))
    for g, mem in GROUPS.items():
        h, q, L, parent = plan[g]; ph = bones[parent].head_local
        az = math.degrees(math.atan2(-(h.x - ph.x), -(h.y - ph.y)))
        out('GROUP %s parent=%s head=(%.4f,%.4f,%.4f) az=%.1f len=%.4f frame_err=%.5f deg members->top %s' % (
            g, parent, h.x, h.y, h.z, az, L, ang(bones[g].matrix_local.to_quaternion(), q),
            ', '.join('%s %.2f' % (m, ang(restq[m], q)) for m in mem)))

    if a.whatif:
        out('WHATIF: nothing saved => OK')
        return
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out_path), relative_remap=True)
    out('SAVED %s => OK' % os.path.abspath(a.out_path))


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback; traceback.print_exc()
        fail('crashed before a verdict', 2)
