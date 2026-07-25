# vrc-skills

> Part of the [Atelier](https://github.com/Ryan6-VRC/atelier) workspace — a code reference, not a standalone product. The docs that govern this code live in the meta-repo.

Reusable Claude Code skills for VRChat avatar/outfit workflows. Skills here are primarily short, triggerable instruction lists that capture judgment and gotchas, not software.

This repo is a self-hosted Claude Code plugin (single-plugin marketplace).

## Skills

The skills are rostered in the meta-repo `README.md` (`## Skills` section); each skill's `description` frontmatter is its canonical trigger.

## Install (local)

```
/plugin marketplace add <path-to>/vrc-skills
/plugin install vrc-skills@vrc
```

## Authoring

New skills drop into `skills/<name>/SKILL.md` and are auto-discovered by the plugin — no registration here. The meta-repo `README.md` (`## Skills`) still needs the skill's row, its key linked to that `SKILL.md` on this repo's `main` (the meta-repo pre-commit hook verifies the key exists and that its link matches). Merge here first: the hook reads this working tree, so a roster row committed ahead of the merge links to a path that is not on `main` yet.

Skills with **ask-the-operator gates** carry the one-line no-operator pointer to the protocol in `workflow.md`, wording kept identical across skills — the validator's `required_no_operator_pointer` constant (`CONVENTIONS.md`) checks each body carries it.
