# tools/validate_skills.py
"""Lint the skills in this repo against CONVENTIONS.md's anatomy contract.

  validate_skills.py            lint every skill directory under skills/
  validate_skills.py DIR...     lint the named skill directories instead

The contract reaches past this repo: a consuming repo's project skills under its
`.claude/skills/` are held to the same anatomy (CONVENTIONS.md "The gate"), and
the workspace's check_prose.py names both enumerations in one invocation. Each
skill's relative links are bounded by the git repo that skill lives in, not by
this one.

Mechanical, load-bearing facts are ERRORS: a skill that would not load (missing
SKILL.md, broken frontmatter, missing name/description, malformed name), a name
that mismatches its directory, an over-cap description, more than one H1, a dead
relative link. Anatomy — the shape CONVENTIONS.md "A skill's anatomy" describes —
is WARNINGS: the description prefix and length band, and the no-operator block
every operator-gated skill owes (matched as the canonical block line, scoped out
for skills in the constants' autonomous list). Routing quality and tool-citation
adequacy are judgment calls the workspace prose-audit adjudicates, not this local
gate. Thresholds, required strings, and the exempt/autonomous lists come from the
fenced constants block in CONVENTIONS.md "## The gate"; this script embeds no
copies. A skill in the exempt list (its sole authority — meta-skills earn the exemption by
being listed, not by mentioning "meta-skill" in prose) gets frontmatter identity checks only.

Frontmatter is parsed with PyYAML, so anything the skill loader would reject is
an ERROR here too. PyYAML is a prerequisite (CONVENTIONS.md "## The gate"): the
gate refuses to run without it rather than reading its own constants block with
a hand-rolled parser that agrees with YAML only on the shapes it was tried on.

Exit 0 when only warnings, 1 on any error,
2 on an internal failure (e.g. the constants block is missing).
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r'^[A-Za-z0-9-]+$')
LINK_RE = re.compile(r'\[[^\]]*\]\(([^)\s]+)[^)]*\)')   # markdown [text](target ...)
H1_RE = re.compile(r'^\s{0,3}#(?!#)(\s|$)')
FENCE_RE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')
NO_OP_RE = re.compile(r'no[- ]operator', re.IGNORECASE)   # the canonical no-op block's signature


class GateError(Exception):
    """Fail-loud error; message names what is missing."""




def _validate_constants(consts):
    """Fail loud (GateError → exit 2) if the constants block is missing a key the
    checks index or gives it a wrong type — so a malformed block is a clean
    internal-failure exit, never a KeyError traceback scored as exit 1."""
    if not isinstance(consts, dict):
        raise GateError('CONVENTIONS.md constants block is not a mapping')

    def need(key, typ, container=consts, where='constants'):
        if key not in container:
            raise GateError(f'CONVENTIONS.md {where} block missing key: {key}')
        if not isinstance(container[key], typ):
            raise GateError(f'CONVENTIONS.md {where} key {key!r} must be '
                            f'{typ.__name__}, got {type(container[key]).__name__}')

    for key in ('description_prefix', 'required_no_operator_pointer'):
        need(key, str)
    need('description_length', dict)
    for sub in ('warn_min', 'warn_max', 'error_max'):
        need(sub, int, consts['description_length'], 'description_length')
    for lst in ('exempt_skills', 'autonomous_skills'):
        if not isinstance(consts.get(lst, []), list):
            raise GateError(f"CONVENTIONS.md '{lst}' must be a list")


def load_constants():
    conv = REPO / 'CONVENTIONS.md'
    if not conv.is_file():
        raise GateError(f'{conv}: CONVENTIONS.md not found — cannot read the constants block')
    text = conv.read_text(encoding='utf-8')
    for block in re.findall(r'^\s{0,3}```ya?ml[^\n]*\n(.*?)^\s{0,3}```\s*$', text, re.M | re.S):
        if 'description_prefix' in block:
            consts = yaml.safe_load(block)
            _validate_constants(consts)
            return consts
    raise GateError(f'{conv}: no fenced yaml constants block found (see "## The gate")')


def strip_fences(lines):
    """Blank out fenced-code lines so heading/content scans skip them; line
    numbering is preserved."""
    out, fence = [], None
    for ln in lines:
        m = FENCE_RE.match(ln)
        if fence:
            out.append('')
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
        elif m:
            fence = m.group(1)
            out.append('')
        else:
            out.append(ln)
    return out


class Findings:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def _emit(self, sev, rel, line, msg):
        loc = f'{rel}:{line}' if line else rel
        print(f'{sev:<5} {loc}: {msg}')

    def error(self, rel, line, msg):
        self.errors += 1
        self._emit('ERROR', rel, line, msg)

    def warn(self, rel, line, msg):
        self.warnings += 1
        self._emit('WARN', rel, line, msg)


def _display(p, home=None):
    """Path relative to the repo it belongs in — REPO for our own skills, the
    consuming repo for a project skill. Without the home argument every finding
    on a project skill prints an absolute machine path, which is now the normal
    case for a consuming repo's skills rather than a hand-run curiosity."""
    for base in (home, REPO):
        if base is not None:
            try:
                return p.relative_to(base).as_posix()
            except ValueError:
                pass
    return p.as_posix()


def repo_root(d):
    """The git repo the skill dir lives in — the boundary its relative links may
    not escape. Deriving this from __file__ instead would call every link in a
    consuming repo's .claude/skills/ an escape, since that skill's docs are in
    ITS repo, not ours. A skill under no repo at all is bounded by itself: our
    REPO is not its containment, and claiming otherwise would be a false error."""
    for p in (d, *d.parents):
        if (p / '.git').exists():   # a file in a worktree, a dir in a clone
            return p
    return REPO if REPO in (d, *d.parents) else d


def parse_frontmatter(lines, out, rel):
    """Return (fields, body_start, desc_line) — fields is None when the block is
    structurally broken (the specific error is already recorded, so downstream
    field checks would only add misleading noise)."""
    if not lines or lines[0].strip() != '---':
        out.error(rel, 1, "missing YAML frontmatter (file must open with '---')")
        return None, 0, None
    close = next((i for i in range(1, len(lines)) if lines[i].strip() in ('---', '...')), None)
    if close is None:
        out.error(rel, 1, "frontmatter opened with '---' but never closed")
        return None, 0, None
    block = lines[1:close]
    desc_line = next((i + 2 for i, ln in enumerate(block) if ln.startswith('description:')), None)

    try:
        data = yaml.safe_load('\n'.join(block))
    except yaml.YAMLError as e:
        mark = getattr(e, 'problem_mark', None)
        line = mark.line + 2 if mark else 1
        problem = getattr(e, 'problem', None) or str(e).splitlines()[0]
        out.error(rel, line, f'frontmatter is not valid YAML: {problem}')
        return None, close + 1, None
    if data is None:
        data = {}
    if not isinstance(data, dict):
        out.error(rel, 1, 'frontmatter must be a mapping (key: value pairs)')
        return None, close + 1, None
    fields = {k: '' if v is None else str(v) for k, v in data.items()}
    return fields, close + 1, desc_line


def check_skill(d, consts, out):
    home = repo_root(d)
    md = d / 'SKILL.md'
    if not md.is_file():
        out.error(_display(d, home), None, 'no SKILL.md')
        return
    rel = _display(md, home)
    lines = md.read_text(encoding='utf-8').splitlines()
    fields, body_start, desc_line = parse_frontmatter(lines, out, rel)

    desc = ''
    if fields is not None:
        name = fields.get('name', '')
        desc = fields.get('description', '')
        if not name:
            out.error(rel, 1, "frontmatter missing required field 'name'")
        elif not NAME_RE.match(name):
            out.error(rel, 1, f"name '{name}' must match [A-Za-z0-9-]+")
        elif name != d.name:
            out.error(rel, 1, f"name '{name}' does not match its directory '{d.name}' "
                              "(the loader keys on the directory)")
        if not desc:
            out.error(rel, 1, "frontmatter missing required field 'description'")
        elif len(desc) > consts['description_length']['error_max']:
            out.error(rel, desc_line, f"description is {len(desc)} chars "
                                      f"(max {consts['description_length']['error_max']})")

    body = lines[body_start:]
    visible = strip_fences(body)

    # Exempt (meta-skills included): frontmatter identity checks only (above). Their bodies use
    # runtime-only links and diverge from the anatomy by design, so the body and anatomy checks
    # below would only misfire. exempt_skills is the SOLE exemption authority — a gate that keyed
    # on a prose substring ("meta-skill") would silently drop error checks (dead links, extra H1)
    # for any skill that merely mentions the word (CONVENTIONS.md "Meta-skills").
    if d.name in consts.get('exempt_skills', []):
        return

    # Mechanical body errors (every non-exempt skill).
    h1s = [i for i, ln in enumerate(visible) if H1_RE.match(ln)]
    if len(h1s) != 1:
        at = body_start + h1s[1] + 1 if len(h1s) > 1 else None
        out.error(rel, at, f'{len(h1s)} H1 headings (need exactly 1)')
    for i, ln in enumerate(visible):
        for m in LINK_RE.finditer(ln):
            tgt = m.group(1).split('#')[0]
            if not tgt or '://' in tgt or tgt.startswith('mailto:'):
                continue
            line = body_start + i + 1
            target = (d / tgt).resolve()
            if not target.exists():
                out.error(rel, line, f"linked file '{tgt}' does not exist")
            elif home != target and home not in target.parents:
                # Name the boundary by path, not by folder name: in a worktree the
                # folder is a disposable machine-local name ("atelier-w10") that
                # tells the reader nothing about which repo is meant.
                out.error(rel, line, f"link '{tgt}' escapes the repo this skill ships in "
                                     f"({home.as_posix()})")

    # Anatomy warnings. Routing quality (does the description name its adjacent
    # siblings?) and tool-citation adequacy are judgment calls the workspace
    # prose-audit adjudicates, not this local gate — see CONVENTIONS.md "The gate".
    prefix = consts['description_prefix']
    if desc and not desc.startswith(prefix):
        out.warn(rel, desc_line, f'description does not start "{prefix}"')
    lo, hi = consts['description_length']['warn_min'], consts['description_length']['warn_max']
    if desc and not lo <= len(desc) <= hi:
        out.warn(rel, desc_line, f'description is {len(desc)} chars (anatomy range {lo}-{hi})')

    # No-operator block: every operator-gated skill routes to the protocol. Match
    # the canonical block line (the pointer named in a "no operator" context, in
    # the intro or at the gate it governs) — not a stray pointer mention, which
    # would let a gated skill pass without an actual block. A skill that runs
    # unattended by design declares itself in autonomous_skills and is exempt.
    pointer = consts['required_no_operator_pointer']
    if d.name not in consts.get('autonomous_skills', []):
        if not any(pointer in ln and NO_OP_RE.search(ln) for ln in visible):
            out.warn(rel, None, f'operator-gated skill lacks the no-operator block '
                                f'("No operator to ask? … {pointer}"); if it runs unattended '
                                'by design, add it to autonomous_skills')


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint skill anatomy against CONVENTIONS.md's contract.")
    ap.add_argument('skill_dirs', nargs='*', metavar='DIR',
                    help='skill directories to lint (default: every directory under skills/)')
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # findings quote UTF-8 prose; pipes default to cp1252 on Windows

    # Checked once here, before any call site: yaml is read by load_constants and
    # again by parse_frontmatter, and an import-time failure would land outside
    # this module's GateError handler as a traceback at exit 1 — the code
    # reserved for lint findings.
    if yaml is None:
        raise GateError('pyyaml not installed — pip install pyyaml '
                        '(prerequisite: CONVENTIONS.md "## The gate")')

    consts = load_constants()
    if args.skill_dirs:
        dirs = []
        for raw in args.skill_dirs:
            d = Path(raw).resolve()
            if not d.is_dir():
                raise GateError(f'{d}: not a directory')
            dirs.append(d)
    else:
        family = REPO / 'skills'
        if not family.is_dir():
            raise GateError(f'{family}: skills/ not found')
        dirs = sorted(p for p in family.iterdir() if p.is_dir())

    out = Findings()
    for d in dirs:
        check_skill(d, consts, out)

    # This line's shape and the 0/1/2 exit codes are a contract the meta-repo's
    # tools/check_prose.py (pass 1) parses; keep both stable. Errors → stdout via
    # Findings; internal failures → stderr + exit 2, so stdout never carries a
    # partial summary on a crash.
    print(f'validate_skills: {len(dirs)} skill(s), {out.errors} error(s), {out.warnings} warning(s)')
    return 1 if out.errors else 0


if __name__ == '__main__':
    # Exit 0 = clean/warnings-only, 1 = lint errors (summary printed), 2 = internal
    # failure. main()'s `sys.exit(1)` raises SystemExit (a BaseException), so it
    # sails past `except Exception` and stays a clean 1; only real crashes → 2.
    try:
        sys.exit(main())
    except GateError as e:
        sys.stderr.write(f'error: {e}\n')
        sys.exit(2)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(2)
