# CircleClar project page

Live page: https://gwwgwd.github.io/CircleClar/

This is a static HTML/CSS/JavaScript page. GitHub Pages publishes the `docs/`
directory of `codex/project-page`; `.nojekyll` bypasses Jekyll processing.
There is no npm build or server-side dependency.

From the repository root, preview with:

```sh
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000`.

## Publishing boundary

Keep only public site content in `docs/`: `index.html`, `.nojekyll`, and `assets/`.
The manuscript source lives in the repository-root `paper/` folder, and the
website generator and maintenance notes live in `website/`. Neither folder is
part of the `/docs` publishing source. The downloadable PDF and displayed
figures remain intentionally public in `docs/assets/`.

GitHub Pages settings remain `codex/project-page` and `/docs`. Moving files outside
that folder removes them from subsequent site deployments; earlier downloaded
copies cannot be withdrawn. Repository visibility is configured independently.

## Updating the page

Paths below are relative to the repository root.

- `website/build_page.py` contains the page template and copy. Run `python3 website/build_page.py`
  to regenerate `docs/index.html` from the template, the active abstract in
  `paper/main.tex`, and `paper/tables/table1_main_qa/table1_main_combined.tex`.
- `docs/assets/site.css` controls typography, colors, and responsive layout.
- `docs/assets/site.js` handles figure enlargement, citation copying, and navigation.
- Replace `docs/assets/paper/circleclar.pdf` when the manuscript changes. The current
  27-page PDF was compiled from `paper/neurips_2026.tex`. In a temporary build copy,
  pass the `table` option to `xcolor` before loading the conference style to avoid
  the source wrapper's package-option clash.
- Re-export the PNG/PDF files in `docs/assets/images/` when paper figures change. The
  overview uses `paper/figures/Figure1_fixed.pdf`; result figures use
  `heapmaptable.pgf` and `policy.pgf`. The web heatmap trims blank margins and uses
  a 7.6pt font for model labels to avoid overlap; its values and colors are unchanged.
- Check the explanatory claims and BibTeX when updating results or publication
  metadata. The current citation uses `@misc` and does not assert an acceptance.

Commit and push changes to `codex/project-page` to update the live page.

## Asset licenses

The manuscript and research figures are the supplied CircleClar material.
The locally hosted Inter font uses the SIL Open Font License in
`docs/assets/fonts/LICENSE.txt`. Feather icons use the MIT license in
`docs/assets/icons/LICENSE.txt`. The page loads no third-party runtime scripts or fonts.
