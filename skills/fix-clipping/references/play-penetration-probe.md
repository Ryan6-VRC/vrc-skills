# Play-mode penetration probe

The motion number for a dynamics fix: how far the body pushes through a garment while the pelvis moves, with a named component off and then on. A documented snippet, not a door: it ran as ad-hoc `execute_code` in the source case and carries the gaps listed at the end. Promote it to a `ReportPenetration` door when a second case needs it.

## What it measures

In avatar space, over a height band around the region, body and garment vertices are binned by azimuth sector and height. Per bin, **depth** is the body's largest radial distance from the avatar's vertical axis minus the garment's smallest: positive means body outside the garment shell there. The headline is the maximum over bins per pose per stage. A cylindrical profile is used because a skirt is an open shell with no inside, so a nearest-surface distance is unsigned and reads a leg below the hem as deep. Alongside it: each chain's tip displacement from its rest capture, and a rest-contact stage (component switched on while standing still, tip movement per chain, where zero means no rest touch).

The pose set is scripted hip motion, not a real dance: rest, side bump left and right, forward thrust, each held to settle, restored to rest between. Amplitudes default to the source case's (5 cm translation, 8 to 10 degrees tilt) and are echoed in the output because they dominate the result; the user cannot tell you how far their hips move in centimetres, so treat them as the assumption the number rests on.

## Preconditions

- Play mode entered by the caller through `manage_editor play` after the play gate (`emulator.md`); the snippet never enters play itself.
- `Application.runInBackground` true and `Time.frameCount` advancing, or nothing solves and the table is flat and wrong (`verify.md`).
- The animator disabled for the probe, so scripted transform writes hold. This also stops FX-driven shapes: read the live blendshape weights first and keep them in the header, since a static anti-clip the FX drives is then absent from the measurement.

## Snippet

Run in one `execute_code` call; it arms an `EditorApplication.update` pump and returns at once. Poll `SessionState.GetString("penprobe")` in later calls until it starts with `done`. Fill the four placeholders.

```csharp
var av = GameObject.Find("<AvatarRoot>");                 // gap: in play the emulator spawns clones; verify this is the local one
string Base(string n){ int i=n.IndexOf('$'); return i<0?n:n.Substring(0,i); } // play-mode bone names carry a $ suffix
var rt = av.transform;
var hips = av.GetComponentsInChildren<Transform>(true).First(t=>Base(t.name)=="<HipsBone>");
var comp = av.GetComponentsInChildren<Component>(true).First(c=>c && Base(c.name)=="<ToggleObject>").gameObject;
string[] chainNames = { <"Skirt_Front", "Skirt_1.L", ...> };
var tips = chainNames.Select(cn=>av.GetComponentsInChildren<Transform>(true).First(t=>Base(t.name)==cn+".005")).ToArray(); // last joint of each chain
var body = av.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(s=>Base(s.name)=="<BodyMesh>");
var garments = av.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(s=>s.gameObject.activeInHierarchy && new[]{<"Dress","SkirtOuter">}.Contains(Base(s.name))).ToArray();
float yMin = 0.70f, yMax = 0.86f, band = 0.02f; int sectors = 24;          // region band in avatar space; adjust from ReportClearance's joint y column
av.GetComponent<Animator>().enabled = false;
var restP = hips.localPosition; var restR = hips.localRotation;
var restTips = tips.Select(t=>rt.InverseTransformPoint(t.position)).ToArray();
List<Vector3> Bake(SkinnedMeshRenderer s){ var m=new Mesh(); s.BakeMesh(m,true); var l=m.vertices.Select(v=>rt.InverseTransformPoint(s.transform.TransformPoint(v))).ToList(); UnityEngine.Object.DestroyImmediate(m); return l; }
float Depth(){
  int bands=(int)((yMax-yMin)/band); var bMax=new float[bands*sectors]; var gMin=new float[bands*sectors];
  for(int i=0;i<gMin.Length;i++){ gMin[i]=float.PositiveInfinity; bMax[i]=float.NegativeInfinity; }
  int Bin(Vector3 p){ if(p.y<yMin||p.y>=yMax) return -1; int b=(int)((p.y-yMin)/band); int s=(int)((Mathf.Atan2(p.x,p.z)+Mathf.PI)/(2*Mathf.PI)*sectors)%sectors; return b*sectors+s; }
  foreach(var p in Bake(body)){ int k=Bin(p); if(k>=0) bMax[k]=Mathf.Max(bMax[k], new Vector2(p.x,p.z).magnitude); }
  foreach(var g in garments) foreach(var p in Bake(g)){ int k=Bin(p); if(k>=0) gMin[k]=Mathf.Min(gMin[k], new Vector2(p.x,p.z).magnitude); }
  float worst=0; for(int i=0;i<gMin.Length;i++) if(!float.IsInfinity(gMin[i])&&!float.IsInfinity(bMax[i])) worst=Mathf.Max(worst, bMax[i]-gMin[i]);
  return worst;
}
var poses = new (string, Vector3, Quaternion)[]{ ("rest",Vector3.zero,Quaternion.identity), ("bumpL",new Vector3(-0.05f,0,0),Quaternion.Euler(0,0,8)), ("bumpR",new Vector3(0.05f,0,0),Quaternion.Euler(0,0,-8)), ("thrust",new Vector3(0,0,0.04f),Quaternion.Euler(-10,0,0)) };
var log = new System.Text.StringBuilder("stage | pose | depthCm | tipMoveCm(max)\n");
int stage=0, pi=0, lf=-1; float st=Time.time; bool on=false; comp.SetActive(false);
EditorApplication.CallbackFunction cb=null;
cb = () => {
  if(!EditorApplication.isPlaying){ EditorApplication.update-=cb; return; }
  if(Time.frameCount==lf) return; lf=Time.frameCount;             // one sample per rendered frame, whatever the fps
  if(Time.time-st<2.5f) return;                                    // gap: fixed hold, not a measured settle
  var p=poses[pi]; float tipMax=tips.Select((t,i)=>(rt.InverseTransformPoint(t.position)-restTips[i]).magnitude).Max();
  log.Append(on?"on":"off").Append(" | ").Append(p.Item1).Append(" | ").Append((Depth()*100).ToString("F1")).Append(" | ").Append((tipMax*100).ToString("F1")).Append('\n');
  SessionState.SetString("penprobe", "running\n"+log);
  hips.localPosition=restP; hips.localRotation=restR;
  pi++; if(pi>=poses.Length){ pi=0; if(on){ EditorApplication.update-=cb; av.GetComponent<Animator>().enabled=true; SessionState.SetString("penprobe","done\n"+log); return; } on=true; comp.SetActive(true); }
  var np=poses[pi]; hips.localPosition=restP+np.Item2; hips.localRotation=restR*np.Item3; st=Time.time;
};
SessionState.SetString("penprobe","armed"); EditorApplication.update+=cb;
return "armed: "+poses.Length+" poses x off/on; poll SessionState penprobe";
```

The first `rest` row of the `on` stage is the rest-contact stage: tip movement there with the component on and the pelvis at rest is a collider touching a chain standing still. Prove that reading with a positive control once per rig: an oversized collider must move a tip in the same row.

## Known gaps, in the order they bite

- **Not two-phase.** A transport timeout on the arming call is harmless, but nothing materialises a RunLog; the result lives in `SessionState` until read.
- **Avatar resolution by name** can pick an emulator clone (mirror or shadow) instead of the local runtime.
- **Fixed hold, no settle detection.** A slow, unfocused Editor may sample before the chain settles; compare `Time.frameCount` deltas across rows before trusting a row.
- **No noise floor.** Off and on run sequentially with hysteresis between poses; an off, on, off ordering would give the floor.
- **Animator off** removes FX-driven shapes from the surface, and a toggle that a clip binds cannot be driven by `SetActive` once the animator returns.
- **One candidate per run.** The source case converged by sweeping eight collider sizes; each is a fresh play session here.
- `VRCPhysBoneCollider` field writes in play need the SDK's `ApplyConfigurationChanges` (non-public) or the runtime keeps the old shape; the snippet toggles the object instead of editing fields for that reason.
