# Product website

Live site: [altwisp.vercel.app](https://altwisp.vercel.app)

This directory contains the static ALTWISP site: HTML, CSS, and JavaScript.
It is maintained alongside the desktop app but excluded from its package.

For a local preview from the repository root:

```powershell
python -m http.server 8000 --directory site
```

Open `http://localhost:8000`. Fonts and GSAP scripts load from external CDNs.
GitHub links require collaborator access while the repository is private.
Committing these files does not deploy a website; configure hosting separately.
