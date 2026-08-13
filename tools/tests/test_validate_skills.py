# tools/tests/test_validate_skills.py
#
# Run:  python -m unittest discover -s tools/tests -t tools/tests
# Not  `-t .` — this directory has no __init__.py, so the repo-root spelling dies with
# "Start directory is not importable".
#
# This is the repo's first test file. It mirrors the meta-repo's convention deliberately
# (stdlib unittest, synthetic fixtures, same discovery invocation) so both gates run the
# same way: pytest is not a prerequisite of this workspace, and CONVENTIONS.md "## The gate"
# declares pyyaml as the only one.
#
# check_skill takes its constants as an argument, so most tests here pass a synthetic CONSTS
# rather than the live CONVENTIONS.md — the gate's behavior is under test, not the workspace's
# current thresholds, which are free to move without turning this suite red.
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import validate_skills as v  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent

CONSTS = {
    'description_prefix': 'Use when',
    'description_length': {'warn_min': 20, 'warn_max': 60, 'error_max': 100},
    'exempt_skills': ['exempted'],
    'autonomous_skills': ['autonomous'],
    'required_no_operator_pointer': 'workflow.md',
    'terminal_section': 'Tools',
}
GOOD_DESC = 'Use when the thing needs doing in a plausible way.'   # inside the 20-60 band
NO_OP_BLOCK = 'No operator to ask? Follow `workflow.md` and proceed.\n'

# TestMainContract subprocesses the real gate, which reads the LIVE CONVENTIONS.md rather
# than the synthetic CONSTS above — so a fixture that is clean under CONSTS still warns
# against the shipped 200-700 band. This one is clean under both.
LIVE_DESC = ('Use when a test needs a description that satisfies the shipped anatomy band '
             'rather than this suite\'s synthetic one, so that a run of the real gate over a '
             'fixture skill reports no findings at all and the exit code under test is the '
             'only thing the assertion can be reading.')


def setUpModule():
    print(f'\ntest_validate_skills: module under test = {v.__file__}')
    print(f'test_validate_skills: repo = {REPO}')


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()   # resolve: the gate resolves link
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)   # targets, and an
        self.out = v.Findings()                                        # 8.3 TEMP forges an
                                                                       # "escapes the repo"
    def skill(self, name, body, repo=None):
        d = (repo or self.tmp) / name
        d.mkdir(parents=True, exist_ok=True)
        (d / 'SKILL.md').write_text(body, encoding='utf-8')
        return d

    def md(self, name='demo', desc=GOOD_DESC, body=None, extra_fm=''):
        body = NO_OP_BLOCK if body is None else body
        return f'---\nname: {name}\ndescription: {desc}\n{extra_fm}---\n\n# {name}\n\n{body}'

    def check(self, d, consts=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            v.check_skill(d, consts or CONSTS, self.out)
        return buf.getvalue()


# ---------------------------------------------------------------- constants

class TestValidateConstants(unittest.TestCase):
    def test_non_mapping_fails_loud(self):
        with self.assertRaises(v.GateError):
            v._validate_constants(['not', 'a', 'mapping'])

    def test_missing_key_is_named(self):
        consts = {k: val for k, val in CONSTS.items() if k != 'description_prefix'}
        with self.assertRaisesRegex(v.GateError, 'description_prefix'):
            v._validate_constants(consts)

    def test_wrong_type_in_a_nested_key_is_named(self):
        consts = {**CONSTS, 'description_length': {**CONSTS['description_length'],
                                                   'error_max': '1024'}}
        with self.assertRaisesRegex(v.GateError, 'error_max'):
            v._validate_constants(consts)


class TestLoadConstants(Fixture):
    def test_missing_conventions_fails_loud(self):
        with mock.patch.object(v, 'REPO', self.tmp), self.assertRaises(v.GateError):
            v.load_constants()

    def test_no_constants_block_fails_loud(self):
        (self.tmp / 'CONVENTIONS.md').write_text('# C\n\nprose only, no fence.\n',
                                                 encoding='utf-8')
        with mock.patch.object(v, 'REPO', self.tmp), self.assertRaises(v.GateError):
            v.load_constants()

    def test_the_live_conventions_block_parses(self):
        # The gate reads its thresholds from CONVENTIONS.md at runtime; a block that stopped
        # parsing would take every skill down with it.
        consts = v.load_constants()
        self.assertEqual(consts['description_prefix'], 'Use when')
        self.assertIn('error_max', consts['description_length'])


# ---------------------------------------------------------------- frontmatter

class TestParseFrontmatter(Fixture):
    def parse(self, text):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = v.parse_frontmatter(text.splitlines(), self.out, 'SKILL.md')
        return result, buf.getvalue()

    def test_no_opening_delimiter(self):
        (fields, _, _), text = self.parse('# Just a heading\n')
        self.assertIsNone(fields)
        self.assertIn('must open', text)

    def test_opened_but_never_closed(self):
        (fields, _, _), text = self.parse('---\nname: demo\n\n# Body\n')
        self.assertIsNone(fields)
        self.assertIn('never closed', text)

    def test_invalid_yaml_is_reported_at_its_own_line(self):
        (fields, _, _), text = self.parse('---\nname: demo\n  bad: [indent\n---\n')
        self.assertIsNone(fields)
        self.assertIn('SKILL.md:3', text)

    def test_non_mapping_frontmatter(self):
        (fields, _, _), text = self.parse('---\n- a list\n- not a mapping\n---\n')
        self.assertIsNone(fields)
        self.assertIn('must be a mapping', text)

    def test_empty_frontmatter_is_a_mapping_of_nothing(self):
        (fields, body_start, _), _ = self.parse('---\n---\n\n# B\n')
        self.assertEqual(fields, {})
        self.assertEqual(body_start, 2)

    def test_null_values_become_empty_strings(self):
        # 'description:' with nothing after it is None in YAML; the gate must treat that as
        # missing, not crash on it or stringify it to "None".
        (fields, _, _), _ = self.parse('---\nname: demo\ndescription:\n---\n')
        self.assertEqual(fields['description'], '')


class TestRepoRoot(Fixture):
    def test_finds_a_git_directory_ancestor(self):
        (self.tmp / '.git').mkdir()
        d = self.skill('demo', 'x')
        self.assertEqual(v.repo_root(d), self.tmp)

    def test_finds_a_git_FILE_ancestor(self):
        # In a linked worktree .git is a file. A skill's links are bounded by the repo it
        # ships in, and getting this wrong calls every legitimate link an escape.
        (self.tmp / '.git').write_text('gitdir: /elsewhere\n', encoding='utf-8')
        d = self.skill('demo', 'x')
        self.assertEqual(v.repo_root(d), self.tmp)

    def test_a_skill_under_no_repo_is_bounded_by_itself(self):
        d = self.skill('demo', 'x')
        self.assertEqual(v.repo_root(d), d)


# ---------------------------------------------------------------- check_skill

class TestCheckSkillIdentity(Fixture):
    def test_missing_skill_md(self):
        d = self.tmp / 'empty'
        d.mkdir()
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('no SKILL.md', text)

    def test_name_must_match_its_directory(self):
        d = self.skill('demo', self.md(name='other'))
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('does not match its directory', text)

    def test_malformed_name_is_an_error(self):
        d = self.skill('demo', self.md(name='has spaces'))
        self.check(d)
        self.assertEqual(self.out.errors, 1)

    def test_missing_description_is_an_error(self):
        d = self.skill('demo', f'---\nname: demo\n---\n\n# demo\n\n{NO_OP_BLOCK}')
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn("missing required field 'description'", text)

    def test_a_conforming_skill_is_silent(self):
        d = self.skill('demo', self.md())
        self.check(d)
        self.assertEqual((self.out.errors, self.out.warnings), (0, 0))


class TestCheckSkillDescriptionBands(Fixture):
    """Boundaries, not just middles: '>' vs '>=' here is a one-character mutation that turns
    a conforming description into an ERROR, and a midpoint test cannot see it."""

    def desc(self, n):
        base = 'Use when '
        return base + 'x' * (n - len(base))

    def test_exactly_error_max_is_not_an_error(self):
        d = self.skill('demo', self.md(desc=self.desc(100)))
        self.check(d)
        self.assertEqual(self.out.errors, 0)

    def test_one_over_error_max_is_an_error(self):
        d = self.skill('demo', self.md(desc=self.desc(101)))
        self.check(d)
        self.assertEqual(self.out.errors, 1)

    def test_the_warn_band_edges_are_inclusive(self):
        for n in (20, 60):
            with self.subTest(length=n):
                out = v.Findings()
                d = self.skill(f'demo{n}', self.md(name=f'demo{n}', desc=self.desc(n)))
                with contextlib.redirect_stdout(io.StringIO()):
                    v.check_skill(d, CONSTS, out)
                self.assertEqual(out.warnings, 0)

    def test_just_outside_the_warn_band_warns(self):
        for n in (19, 61):
            with self.subTest(length=n):
                out = v.Findings()
                d = self.skill(f'demo{n}', self.md(name=f'demo{n}', desc=self.desc(n)))
                with contextlib.redirect_stdout(io.StringIO()):
                    v.check_skill(d, CONSTS, out)
                self.assertEqual(out.warnings, 1)

    def test_wrong_prefix_warns(self):
        d = self.skill('demo', self.md(desc='Invoke this whenever the thing needs doing.'))
        text = self.check(d)
        self.assertEqual(self.out.warnings, 1)
        self.assertIn('Use when', text)


class TestCheckSkillBody(Fixture):
    def test_zero_h1_is_an_error(self):
        d = self.skill('demo', f'---\nname: demo\ndescription: {GOOD_DESC}\n---\n\n'
                               f'no heading here\n\n{NO_OP_BLOCK}')
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('0 H1 headings', text)

    def test_two_h1s_is_an_error(self):
        d = self.skill('demo', self.md(body=f'# Second H1\n\n{NO_OP_BLOCK}'))
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('2 H1 headings', text)

    def test_a_fenced_h1_is_not_a_heading(self):
        # Skills document markdown; a '# ' inside an example fence must not count, and the
        # blanking (rather than deleting) is what keeps the line numbers below honest.
        d = self.skill('demo', self.md(body=f'```md\n# Not a real heading\n```\n\n{NO_OP_BLOCK}'))
        self.check(d)
        self.assertEqual(self.out.errors, 0)

    def test_dead_relative_link_is_an_error_at_its_line(self):
        (self.tmp / '.git').mkdir()
        d = self.skill('demo', self.md(body='padding\n\npadding\n\n'
                                            'See [the notes](notes/missing.md).\n\n'
                                            + NO_OP_BLOCK))
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('SKILL.md:12', text)
        self.assertIn('does not exist', text)

    def test_a_fenced_link_is_not_scanned(self):
        (self.tmp / '.git').mkdir()
        d = self.skill('demo', self.md(body='```md\n[example](nowhere/at/all.md)\n```\n\n'
                                            + NO_OP_BLOCK))
        self.check(d)
        self.assertEqual(self.out.errors, 0)

    def test_a_link_escaping_the_owning_repo_is_an_error(self):
        (self.tmp / 'repo').mkdir()
        (self.tmp / 'repo' / '.git').mkdir()
        (self.tmp / 'outside.md').write_text('# Outside\n', encoding='utf-8')
        d = self.skill('demo', self.md(body='See [outside](../../outside.md).\n\n' + NO_OP_BLOCK),
                       repo=self.tmp / 'repo')
        text = self.check(d)
        self.assertEqual(self.out.errors, 1)
        self.assertIn('escapes the repo', text)

    def test_absolute_and_anchor_links_are_not_checked(self):
        (self.tmp / '.git').mkdir()
        d = self.skill('demo', self.md(body='[web](https://example.invalid/x.md) and '
                                            '[anchor](#section)\n\n' + NO_OP_BLOCK))
        self.check(d)
        self.assertEqual(self.out.errors, 0)


class TestCheckSkillExemptions(Fixture):
    def test_exempt_skill_gets_identity_checks_only(self):
        # Its body diverges from the anatomy by design: two H1s, a dead link, no no-operator
        # block. None of that is a finding; a broken NAME still is.
        d = self.skill('exempted', f'---\nname: exempted\ndescription: {GOOD_DESC}\n---\n\n'
                                   '# One\n\n# Two\n\n[dead](nope.md)\n')
        self.check(d)
        self.assertEqual((self.out.errors, self.out.warnings), (0, 0))

    def test_exemption_does_not_extend_to_frontmatter_identity(self):
        d = self.skill('exempted', f'---\nname: wrong\ndescription: {GOOD_DESC}\n---\n\n# X\n')
        self.check(d)
        self.assertEqual(self.out.errors, 1)

    def test_a_non_exempt_control_is_still_fully_checked(self):
        # The both-directions half: a mutation widening the exempt test (`if exempt:`) would
        # silence every skill in the workspace, and a single-skill fixture would not notice.
        d = self.skill('control', self.md(name='control', body='# Second H1\n\n' + NO_OP_BLOCK))
        self.check(d)
        self.assertEqual(self.out.errors, 1)

    def test_autonomous_skill_owes_no_no_operator_block(self):
        d = self.skill('autonomous', self.md(name='autonomous', body='Runs unattended.\n'))
        self.check(d)
        self.assertEqual(self.out.warnings, 0)

    def test_a_gated_skill_without_the_block_warns(self):
        d = self.skill('demo', self.md(body='No block here.\n'))
        text = self.check(d)
        self.assertEqual(self.out.warnings, 1)
        self.assertIn('no-operator block', text)

    def test_the_pointer_alone_is_not_a_no_operator_block(self):
        # The check is `pointer in ln AND /no.operator/` on the SAME line. Mutating that to
        # `or` lets any skill that merely cites workflow.md pass without a block — precisely
        # what the code comment says the conjunction exists to prevent.
        d = self.skill('demo', self.md(body='Sequencing lives in `workflow.md`.\n'))
        text = self.check(d)
        self.assertEqual(self.out.warnings, 1)
        self.assertIn('no-operator block', text)


# ---------------------------------------------------------------- shared helper

class TestStripFences(unittest.TestCase):
    """Byte-identical to the meta-repo's copy in tools/check_prose.py. Mirrored here so a
    divergence in either turns something red; the meta-repo suite holds the drift test that
    compares the two sources directly."""

    def test_blanks_fenced_content_and_preserves_line_count(self):
        src = ['before', '```python', 'code = 1', '```', 'after']
        self.assertEqual(v.strip_fences(src), ['before', '', '', '', 'after'])

    def test_tilde_fences_are_fences_too(self):
        self.assertEqual(v.strip_fences(['a', '~~~', 'hidden', '~~~', 'b']),
                         ['a', '', '', '', 'b'])

    def test_a_shorter_or_mismatched_run_does_not_close_the_fence(self):
        src = ['````', '~~~', '```', 'still inside', '````', 'out']
        self.assertEqual(v.strip_fences(src), ['', '', '', '', '', 'out'])


# ---------------------------------------------------------------- entry point

class TestMainContract(Fixture):
    """The summary line and the 0/1/2 exit codes are a contract the meta-repo's
    check_prose.py pass 1 parses (its VALIDATE_SUMMARY_RE and the exit-code branches around
    it). Pinned from the producer's side here: tidying the f-string below would otherwise
    leave both repos' suites green while the parent gate silently stops adjudicating."""

    SUMMARY_RE = r'(?m)^validate_skills: \d+ skill\(s\), \d+ error\(s\), \d+ warning\(s\)$'

    def run_gate(self, *dirs):
        p = subprocess.run([sys.executable, str(REPO / 'tools' / 'validate_skills.py'),
                            *[str(d) for d in dirs]],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        return p.returncode, p.stdout, p.stderr

    def test_clean_run_exits_zero_with_the_summary_line(self):
        d = self.skill('demo', self.md(desc=LIVE_DESC))
        rc, stdout, stderr = self.run_gate(d)
        self.assertEqual(rc, 0, stdout + stderr)
        self.assertRegex(stdout, self.SUMMARY_RE)
        self.assertIn('validate_skills: 1 skill(s), 0 error(s), 0 warning(s)', stdout)

    def test_findings_exit_one_with_a_consistent_tally(self):
        d = self.skill('demo', self.md(name='mismatched'))
        rc, stdout, stderr = self.run_gate(d)
        self.assertEqual(rc, 1, stdout + stderr)
        self.assertRegex(stdout, self.SUMMARY_RE)
        # The parent cross-checks the tally against the emitted lines; they must agree.
        self.assertEqual(stdout.count('\nERROR') + stdout.startswith('ERROR'), 1)
        self.assertIn('1 error(s)', stdout)

    def test_internal_failure_exits_two_and_prints_no_summary(self):
        # "traceback on stderr, never a partial summary" is contract text the parent relies
        # on: a summary line on a crashed run would be adopted as a real tally.
        rc, stdout, stderr = self.run_gate(self.tmp / 'does-not-exist')
        self.assertEqual(rc, 2)
        self.assertNotIn('validate_skills:', stdout)
        self.assertIn('error:', stderr)

    def test_one_finding_is_always_one_line(self):
        # An authored newline (YAML escape or block scalar) inside a name used to split one
        # finding across two ERROR-prefixed lines, making the tally disagree with the emitted
        # lines and reading, to the parent, as this gate having crashed mid-run.
        forged = 'bad' + chr(92) + 'nERROR forged/SKILL.md:1: injected'
        d = self.skill('demo', f'---\nname: "{forged}"\ndescription: {GOOD_DESC}\n---\n\n'
                               f'# demo\n\n{NO_OP_BLOCK}')
        rc, stdout, stderr = self.run_gate(d)
        self.assertEqual(rc, 1, stdout + stderr)
        self.assertEqual(len([l for l in stdout.splitlines() if l.startswith('ERROR')]), 1)
        self.assertIn('1 error(s)', stdout)

    def test_the_live_skills_tree_is_clean(self):
        rc, stdout, stderr = self.run_gate()
        self.assertEqual(rc, 0, stdout + stderr)
        self.assertRegex(stdout, self.SUMMARY_RE)


if __name__ == '__main__':
    unittest.main()
