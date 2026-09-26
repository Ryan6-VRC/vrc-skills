# Editor A/B of weight variants

How the operator compares weight variants on the composed row in the Editor. A documented procedure over `execute_code`, not a door; promote it to a Unity door when a second case needs one. One agent drives the Editor, pinned before the first call (CLAUDE.md rule 9).

## 1. Build and export the variants

- Each variant is `<stem>_ab_<tag>.blend` beside the venue blend, written from it by the doors' `--out`, so the linked body still resolves and the `recipe:` lines are the whole record of what differs. Record the venue blend's sha256 before building the first.
- Export each with `export_unity_fbx`, scoped as the venue blend's own export is (`--armature`), to `Assets/Agent/Scratch/<task>/<stem>_ab_<tag>.fbx`, then `refresh_unity`. Scratch is disposable, and nothing durable may reference it (`LAYOUT.md`).

## 2. Confirm the scene can be thrown away

Edit mode, the row's scene active, and `SceneManager.GetActiveScene().isDirty` false. The teardown reopens the scene from disk and discards every unsaved change in it. A dirty scene holds either someone's unsaved work or a bake's residue, since `AvatarBake` (a bake-mode `ReportComposition`) dirties the scene with no intended change, and the flag cannot tell the two apart: ask the operator before building over one.

## 3. Match each variant's import to the live mesh

Per variant, before any check: `EditorUtility.CopySerialized(liveImporter, variantImporter)` then `variantImporter.SaveAndReimport()`, both `ModelImporter`s from `AssetImporter.GetAtPath`. A fresh import takes Unity's defaults, and blendshape normals at `Calculate` split vertices, so the variant's vertex count differs from the live mesh's until the live FBX's conformed settings are copied onto it. The live FBX is the same blend's owned export, so its settings are the right ones; a vendor FBX's settings never go onto an owned export (`blender.md`, orientation).

## 4. Check, then stage

Against the live renderer each variant stands in for, resolved by path under the row's instance, stop on any mismatch:

- the variant FBX's `SkinnedMeshRenderer.bones` names, in order, equal the live FBX's;
- vertex, blendshape and submesh counts equal the live `sharedMesh`'s;
- a weights-only variant moves no vertex from the live mesh's position; a pushed variant moves only the pushed region.

Then `Object.Instantiate` the live renderer's GameObject under the same parent, name it `AB_<renderer>_<tag>`, `SetActive(false)`, and set its `sharedMesh` to the variant mesh and its `bones` to the live renderer's. Materials and the live blendshape weights come with the copy.

A fold variant has fewer bones than an unfolded live mesh and fails the bone-order check: bind its bones by name from the live rig instead, which works only while every variant bone exists there.

The copy is not the target of the row's Modular Avatar reactions (a Delete, a Set, a toggle), which reference the original renderer: it shows geometry the row cuts and misses shapes the row drives. Tell the operator what to disregard.

**Never save the scene.** It does not read dirty for the copies, and a save stores them anyway.

## 5. Present

Per renderer: each object, which one is active, and one line on what its weights do differently; the spot and the motion to look at; what the copy lacks. Only one of each pair is active at a time.

## 6. Tear down

`EditorSceneManager.OpenScene(<the scene's own path>, OpenSceneMode.Single)` drops the copies, the swaps and whatever a bake dirtied; confirm `isDirty` false and no `AB_` object left. Delete the scratch folder with `AssetDatabase.DeleteAsset`, and every `_ab_` blend except the pick.

## 7. Promote the pick

Confirm the venue blend still hashes as recorded in step 1; a changed hash means someone edited it since, so rebuild the pick from it by its recipe lines. Copy the pick's `_ab_` blend over the venue blend, confirm the venue blend now hashes as the pick, and delete the pick's `_ab_` blend. The recipe lines say what was done, so no weight diff is needed. If the operator keeps the live mesh, nothing is promoted.
