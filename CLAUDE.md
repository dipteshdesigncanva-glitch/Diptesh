# CLAUDE.md

This repo is a collection of Claude Code skills for making videos, animation and 3D for the web with code. There is no app here yet. The skills live in `.claude/skills/` and are tracked in `skills-lock.json`.

## Installed skills

| Skill | Source | Use it for |
|---|---|---|
| `video-editing` | `heygen-com/hyperframes` | HyperFrames CLI: HTML-based compositions, preview, lint/check, local and cloud rendering |
| `remotion-best-practices` | `remotion-dev/skills` | Entry point for any Remotion task; routes to the skills below |
| `remotion-create` | `remotion-dev/skills` | Start a new Remotion project or composition |
| `remotion-markup` | `remotion-dev/skills` | Content, animation and effects in Remotion React code |
| `remotion-captions` | `remotion-dev/skills` | Transcribe, display and animate captions |
| `remotion-multimedia` | `remotion-dev/skills` | Audio/video handling with Mediabunny |
| `remotion-maps` | `remotion-dev/skills` | Map animations |
| `remotion-interactivity` | `remotion-dev/skills` | Write markup that Remotion Studio can edit interactively |
| `remotion-studio` | `remotion-dev/skills` | Preview a video in Remotion Studio |
| `remotion-render` | `remotion-dev/skills` | Export a video |
| `remotion-saas` | `remotion-dev/skills` | Build an app on top of Remotion |
| `remotion-docs` | `remotion-dev/skills` | Look up current Remotion docs |
| `remotion-upgrade` | `remotion-dev/skills` | Upgrade Remotion packages |

### Animation (GSAP, official)

From `greensock/gsap-skills`: `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `gsap-react`, `gsap-frameworks`, `gsap-utils`, `gsap-performance`.

### Web design, animation and 3D

From `freshtechbro/claudedesignskills`:

- **3D:** `threejs-webgl`, `react-three-fiber`, `babylonjs-engine`, `playcanvas-engine`, `aframe-webxr`, `lightweight-3d-effects`, `spline-interactive`, `blender-web-pipeline`, `substance-3d-texturing`, `web3d-integration-patterns`
- **2D and UI animation:** `animejs`, `motion-framer`, `react-spring-physics`, `lottie-animations`, `rive-interactive`, `pixijs-2d`, `animated-component-libraries`
- **Scroll and page transitions:** `locomotive-scroll`, `scroll-reveal-libraries`, `barba-js`
- **Design:** `modern-web-design`

Two skills from that pack are deliberately not installed: its `gsap-scrolltrigger` (the official GreenSock one is used instead) and its `skill-creator` (Anthropic's built-in one already covers this).

## Choosing a tool

- If the user says "Remotion", or wants React components, start with `remotion-best-practices`.
- If the user says "HyperFrames", or wants HTML compositions or HeyGen/Lambda/Cloud Run rendering, use `video-editing`.
- If they named neither, ask which one they want before scaffolding anything.

## Working rules

- Put each video project in its own folder at the repo root (for example `videos/<project-name>/`). Don't scaffold into the repo root, and never inside `.claude/`.
- Open a preview (Remotion Studio or `npx hyperframes preview`) as soon as the project runs. Get the user's approval before doing a final render.
- Don't commit rendered output (`out/`, `*.mp4`, `*.mov`, `*.webm`) or `node_modules/`.
- Both toolchains need Node.js and FFmpeg. HyperFrames needs Node.js 22 or newer.

## Managing skills

- Install or update skills with the `skills` CLI so `skills-lock.json` stays in sync. Don't edit the installed skill files by hand, because the next update overwrites them.
  - Add: `npx skills add <owner/repo> --agent claude-code -y`
  - Update: `npx skills update -p -y`
  - List: `npx skills list`
- Put custom skills in `.claude/skills/<name>/SKILL.md`, with `name` and `description` in the YAML frontmatter.
- Commit the skill folders and `skills-lock.json` together.
