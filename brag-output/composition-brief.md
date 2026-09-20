# Hyperframes Composition Brief: ALTWISP

## Objective
Create a short launch-style brag video for ALTWISP that demonstrates the real voice-dictation flow as a premium, quiet Windows utility.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material
- Project root: `D:/SELF_PROJECT/ALTWISP`
- Primary files read: `README.md`, `electron-app/renderer/index.html`, `electron-app/renderer/styles.css`, `electron-app/renderer/app.js`, `electron-app/renderer/overlay.html`, `site/index.html`, `site/styles.css`
- Product name: ALTWISP
- Tagline / strongest claim: “Voice, uninterrupted.” / “Your fastest interface is already with you.”
- Key UI or visual moment to recreate: Ctrl + Windows activates the orb and dashboard Listening state; the completed transcript appears in “Your latest words.”
- Copy that must appear verbatim:
  - “Speak. Move. Keep going.”
  - “One gesture. Zero friction.”
  - “Make space for the next thought.”
  - “Voice, uninterrupted.”

## Creative Direction
- Tone preset: polished
- Creative direction: premium cinematic product film for a quiet Windows utility
- Interpretation: large restrained type, confident holds, faithful product UI, and minimal motion-matched audio.
- Angle: ALTWISP protects the user’s train of thought by turning one shortcut and a spoken sentence into polished text without a context switch.
- Hook: Spoken-thought copy and the real orb wake on a dark signal field.
- Outro / punchline: ALTWISP — Voice, uninterrupted.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Waveform/equalizer clichés
  - Claims that ALTWISP answers questions or executes commands

## Visual Identity
- Background: `#07091a`, `#101928`
- Text: `#f3f4f0` on dark; `#111827` in dashboard UI
- Accent: `#536dfe`, `#8d67ff`, `#00e4d0`
- Display font: Space Grotesk when a local font is available; otherwise bundled Inter
- Body font: Inter / Segoe UI
- Visual references from the project: violet-cyan orb, dark navy sidebar, light dashboard, rounded status card, Ctrl + Win keycaps, subtle grid and glow

## Storyboard
Use `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. The thought — 3s — “Speak. Move. Keep going.” and orb wake.
2. One gesture — 5.75s — Ctrl + Win interaction, Listening status, orb response.
3. Words land in context — 6s — dashboard transcript types in and status resolves.
4. Brand lockup — 5.25s — ALTWISP and “Voice, uninterrupted.” final hold.

## Audio
- Audio role: cinematic support with restrained professional accents
- Audio arc: clean opening, slight lift during capture, warm resolution, fade under final lockup
- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`
- Music treatment: baseline volume 0.26; preserve dialogue-free clarity; fade out over the final 2.5 seconds
- Music cue guidance: bundled preset at `C:/Users/BATMAN/.codex/skills/brag/assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`; favor 8.74s, 13.11s, and 17.47s for major reveals where pacing permits
- Audio-reactive treatment: subtle orb glow/background depth response to RMS/bass; no waveform graphics
- Audio-coupled moments:
  - Ctrl + Win press — precise low-risk click
  - Listening state — subtle interface accent
  - Transcript completion — warm success cue
  - Final logo — restrained low impact
- SFX selection guidance: choose low/medium high-frequency-risk sounds appropriate for a polished tone; use only 2–3 cues
- SFX analysis guidance: `C:/Users/BATMAN/.codex/skills/brag/assets/sfx/sfx-analysis.md`
- Exact SFX choice: Hyperframes should choose filenames, timestamps, density, and volume based on implemented animation
- Audio files: copy selected files into `brag-output/composition/assets/`

## Hyperframes Instructions
Use `hyperframes-core`, `hyperframes-animation`, `hyperframes-creative`, `hyperframes-keyframes`, and `hyperframes-cli`. This is the `/brag` workflow; do not enter the generic Hyperframes intent interview.

Requirements:
- Show the actual ALTWISP user flow and faithfully recreate its dashboard language.
- Use the real orb image from `docs/assets/altwisp-orb.png`.
- Keep all text readable and the duration exactly 20 seconds.
- Include the selected music and sparse SFX.
- Use cue metadata only where it supports readability and story.
- Keep animation seek-safe and deterministic with one paused GSAP timeline.
- Use local assets only.
- Run `npx hyperframes check` before preview.
