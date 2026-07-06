# vrc-skills

> Part of the [Atelier](https://github.com/Ryan6-VRC/atelier) workspace — a code reference, not a standalone product. The docs that govern this code live in the meta-repo.

Reusable Claude Code skills for VRChat avatar/outfit workflows. Skills here are primarily short, triggerable
instruction lists that capture judgment and gotchas, not software.

This repo is a self-hosted Claude Code plugin (single-plugin marketplace).

## Skills

The skills and their triggers are listed in the meta-repo `TOOLS.md` (vrc-skills section);
each skill's `description` frontmatter is its canonical trigger.

## Install (local)

```
/plugin marketplace add <path-to>/vrc-skills
/plugin install vrc-skills@vrc
```

## Authoring

New skills drop into `skills/<name>/SKILL.md` and are auto-discovered by the plugin — no registration
here. The meta-repo `TOOLS.md` still needs the skill's row (its pre-commit hook verifies the key exists).
