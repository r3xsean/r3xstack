# r3xstack

My personal agent skills.

**Requires [T3 Code](https://github.com/pingdotgg/t3code).** Several skills hand work to models from other providers through T3 Code's delegation tools, so they don't run in plain Claude Code or Codex.

> Until a generated overview is available, this README lists the skills.

## Skills

| Skill | What it's for |
|---|---|
| [`back-and-forth`](skills/back-and-forth/) | Use when the user says "go back and forth with" another model. |
| [`code-loop`](skills/code-loop/) | Use when the user says "code loop with" a model, or another skill asks for a code loop. |
| [`design-process`](skills/design-process/) | Use when designing, redesigning or polishing a product's UI; when running a design council on screenshots; or when recording the user's reactions to designs. |
| [`grill-me`](skills/grill-me/) | Use when the user says "grill me", or another skill asks for a grill. |
| [`incorporate`](skills/incorporate/) | Use when the user says "incorporate this into my workflow". |
| [`make-verifiable`](skills/make-verifiable/) | Use when the user asks to make a repo verifiable, or another skill needs a repo's verify skill created, extended or repaired. |
| [`model-audit`](skills/model-audit/) | Use when the user says "audit the models" in a workflow, or another skill hands over a model launch. |
| [`second-look`](skills/second-look/) | Use when the user asks to get a second look at something, or another skill asks for a second look. |
| [`see-it-through`](skills/see-it-through/) | Use when the user says "see it through". |
| [`transcribe-youtube`](skills/transcribe-youtube/) | Transcribe a YouTube video into a timestamped text file. Use when a user provides a YouTube URL and needs its transcript, captions, quotes, or searchable video text. |
| [`writing-steering-files`](skills/writing-steering-files/) | Create or edit a steering file — a skill, an AGENTS.md/CLAUDE.md, or a durable agent prompt — through a grill-and-distill loop. Use whenever writing a new skill, AGENTS.md, automation prompt, or product system prompt, changing an existing one, or when another skill needs a steering file authored. |

## Install

```bash
git clone https://github.com/r3xsean/r3xstack.git
mkdir -p ~/.agents/skills ~/.claude/skills
cp -R r3xstack/skills/* ~/.agents/skills/   # Codex
cp -R r3xstack/skills/* ~/.claude/skills/   # Claude Code
```

On Windows (PowerShell):

```powershell
git clone https://github.com/r3xsean/r3xstack.git
New-Item -ItemType Directory -Force "$HOME\.agents\skills", "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force r3xstack\skills\* "$HOME\.agents\skills\"
Copy-Item -Recurse -Force r3xstack\skills\* "$HOME\.claude\skills\"
```

To update, `git -C r3xstack pull` and copy again. Copying never deletes: when a skill is removed or renamed here, delete its old folder from your skills folders yourself.

## How this repo works

It's published automatically from my private skills source: a job checks every five minutes and, when the skills have changed, publishes them as one commit. Changes go into the private source first, so open an issue rather than a pull request.

## License

[MIT](LICENSE)
