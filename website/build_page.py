from pathlib import Path
from html import escape
import json
import re
import struct

SITE = Path(__file__).resolve().parents[1] / 'docs'
PAPER = SITE.parent / 'paper'

def icon(name):
    source = (SITE / 'assets/icons' / f'{name}.svg').read_text().strip()
    assert '<script' not in source and 'onload=' not in source
    return source.replace('<svg ', '<svg aria-hidden="true" focusable="false" ', 1)

def read_group(source, start):
    assert source[start] == '{'
    depth = 0
    for end in range(start, len(source)):
        if source[end] == '{':
            depth += 1
        elif source[end] == '}':
            depth -= 1
            if depth == 0:
                return source[start + 1:end], end + 1
    raise ValueError('Unbalanced table value')

table_source = (PAPER / 'tables/table1_main_qa/table1_main_combined.tex').read_text()
cells = []
for match in re.finditer(r'\\fem\{', table_source):
    cursor = match.end() - 1
    values = []
    for _ in range(3):
        group, cursor = read_group(table_source, cursor)
        values.append(float(re.search(r'\d+\.\d+', group).group()))
    cells.append(values)
assert len(cells) == 48, len(cells)

datasets = [
    ('AmbigQA-HQ', '100 curated questions'),
    ('AmbigQA', '1,000 questions'),
    ('AMBROSIA', '96 Text-to-SQL requests'),
]
methods = ['ICE', 'Sampling-50', '1-Enumeration', 'CircleClar']
models = ['Qwen3-4B', 'Qwen3-30B-A3B', 'GPT-5.4-mini', 'GPT-5.5']
wins = 0

def table_body(detailed=False):
    global wins
    groups = []
    for dataset_index, (dataset, size) in enumerate(datasets):
        records = cells[dataset_index * 16: (dataset_index + 1) * 16]
        best = [max(records[method * 4 + model][0] for method in range(4)) for model in range(4)]
        rows = []
        for method_index, method in enumerate(methods):
            row = '<tr class="ours">' if method == 'CircleClar' else '<tr>'
            if method_index == 0:
                row += f'<th scope="rowgroup" rowspan="4" class="dataset-label">{dataset}<span class="dataset-size">{size}</span></th>'
            row += f'<th scope="row" class="method-label">{method}</th>'
            for model_index in range(4):
                mean, sd, em = records[method_index * 4 + model_index]
                number = f'{mean:.2f}'
                if mean == best[model_index]:
                    number = f'<strong>{number}</strong>'
                    if method == 'CircleClar' and not detailed:
                        wins += 1
                if detailed:
                    number += f' ± {sd:.2f}<span class="cell-em">EM: {em:.2f}%</span>'
                row += f'<td>{number}</td>'
            rows.append(row + '</tr>')
        groups.append('<tbody>\n' + '\n'.join(rows) + '\n</tbody>')
    return '\n'.join(groups)

simple_table = table_body()
full_table = table_body(detailed=True)
assert wins == 7, wins
header = '<thead><tr><th scope="col">Dataset</th><th scope="col">Method</th>' + ''.join(f'<th scope="col">{model}</th>' for model in models) + '</tr></thead>'

abstract_source = (PAPER / 'main.tex').read_text()
abstract = re.search(r'\\looseness=-1 (Ambiguous inputs.*?correspondence\.)', abstract_source).group(1)
abstract = abstract.replace(r'\circleclar{}', 'CircleClar').replace('answer--clarification--answer', 'answer–clarification–answer')
abstract = escape(abstract)
abstract = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', abstract)

bibtex = r'''@misc{tang2026clarification,
  title  = {What Is a Clarification? Estimating Model-Dependent Input Ambiguity},
  author = {Tang, Jingqin and Tomov, Tim and Schmidt, Sebastian and
            Fuchsgruber, Dominik and G{\"u}nnemann, Stephan},
  year   = {2026}
}'''

def figure(name, title, alt, width, height, eager=False):
    loading = '' if eager else ' loading="lazy"'
    width, height = struct.unpack('>II', (SITE / 'assets/images' / f'{name}.png').read_bytes()[16:24])
    return f'''<a class="figure-link" href="assets/images/{name}.png" data-figure data-title="{escape(title, quote=True)}" data-original="assets/images/{name}.pdf" aria-haspopup="dialog">
      <img src="assets/images/{name}.png" width="{width}" height="{height}" alt="{escape(alt, quote=True)}"{loading} decoding="async">
      <span class="figure-hint">{icon('maximize-2')} View full size</span>
    </a>'''

metadata = {
    '@context': 'https://schema.org', '@type': 'ScholarlyArticle',
    'name': 'What Is a Clarification? Estimating Model-Dependent Input Ambiguity',
    'url': 'https://gwwgwd.github.io/CircleClar/',
    'author': [{'@type': 'Person', 'name': name} for name in ['Jingqin Tang', 'Tim Tomov', 'Sebastian Schmidt', 'Dominik Fuchsgruber', 'Stephan Günnemann']],
    'about': ['Input ambiguity', 'Clarification', 'Language models'],
}

document = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CircleClar — What Is a Clarification?</title>
  <meta name="description" content="CircleClar estimates model-dependent input ambiguity through answer–clarification–answer consistency cycles. Research from the Technical University of Munich.">
  <meta name="theme-color" content="#121a26">
  <link rel="canonical" href="https://gwwgwd.github.io/CircleClar/">
  <meta property="og:type" content="website">
  <meta property="og:title" content="What Is a Clarification? Estimating Model-Dependent Input Ambiguity">
  <meta property="og:description" content="CircleClar: a black-box method for estimating model-realizable answer sets.">
  <meta property="og:url" content="https://gwwgwd.github.io/CircleClar/">
  <meta property="og:image" content="https://gwwgwd.github.io/CircleClar/assets/images/overview.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="citation_title" content="What Is a Clarification? Estimating Model-Dependent Input Ambiguity">
  <meta name="citation_author" content="Jingqin Tang">
  <meta name="citation_author" content="Tim Tomov">
  <meta name="citation_author" content="Sebastian Schmidt">
  <meta name="citation_author" content="Dominik Fuchsgruber">
  <meta name="citation_author" content="Stephan Günnemann">
  <meta name="citation_pdf_url" content="https://gwwgwd.github.io/CircleClar/assets/paper/circleclar.pdf">
  <link rel="preload" href="assets/fonts/InterVariable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="assets/site.css">
  <script type="application/ld+json">{json.dumps(metadata, ensure_ascii=False)}</script>
  <script src="assets/site.js" defer></script>
</head>
<body id="top">
  <a class="skip-link" href="#overview">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="#top" aria-label="CircleClar — top of page">{icon('rotate-cw')}<span>CircleClar</span></a>
      <nav class="site-nav" aria-label="Page sections">
        <a href="#overview" aria-current="location">Overview</a>
        <a href="#abstract">Abstract</a>
        <a href="#results">Results</a>
        <a href="#bibtex">BibTeX</a>
      </nav>
    </div>
  </header>
  <main>
    <section class="paper-header" aria-labelledby="paper-title">
      <h1 id="paper-title">What Is a Clarification<span class="title-question">?</span></h1>
      <p class="paper-subtitle">Estimating Model-Dependent Input Ambiguity</p>
      <p class="authors"><span>Jingqin Tang</span><span>Tim Tomov</span><span>Sebastian Schmidt</span><span>Dominik Fuchsgruber</span><span>Stephan Günnemann</span></p>
      <p class="affiliation">Technical University of Munich</p>
      <div class="resource-links">
        <a class="button button-primary" href="assets/paper/circleclar.pdf" target="_blank" rel="noopener">{icon('file-text')} Paper<span class="visually-hidden"> (PDF, opens in a new tab)</span></a>
        <a class="button" href="https://github.com/GWWGWD/CircleClar" target="_blank" rel="noopener">{icon('code')} Code<span class="visually-hidden"> (opens in a new tab)</span></a>
        <a class="button" href="#bibtex">{icon('copy')} BibTeX</a>
      </div>
    </section>
    <section id="overview" class="overview-section container" aria-label="Overview">
      <p class="overview-lead">An ambiguous question has several valid answers, but a given model knows only some of them. CircleClar estimates which, by checking whether each candidate answer survives an answer → clarification → answer round trip.</p>
      <figure class="overview-figure">
        {figure('overview', 'World ambiguity, clarifications, and CircleClar', 'Three panels distinguish world ambiguity from model ambiguity, show the correspondence between valid answers and clarification classes, and illustrate how CircleClar filters candidates using answer–clarification–answer recovery.', 3600, 1040, eager=True)}
      </figure>
      <div class="idea-grid">
        <article class="idea idea-problem">
          <p class="idea-label">(a) the problem</p>
          <h3>World ≠ model ambiguity</h3>
          <p>An input determines which answers are valid. The alternatives a model can realize depend on the model.</p>
        </article>
        <article class="idea idea-theory">
          <p class="idea-label">(b) the idea</p>
          <h3>Valid answers ↔ clarification classes</h3>
          <p>Under uniqueness, faithfulness, and answer equivalence, valid answers and equivalence classes of clarifications correspond one-to-one.</p>
        </article>
        <article class="idea idea-method">
          <p class="idea-label">(c) the method</p>
          <h3>Keep the answers that come back</h3>
          <p>Propose candidates, write a clarification for each, and re-answer. Keep candidates that pass the recovery and frequency checks.</p>
        </article>
      </div>
    </section>
    <section id="abstract" class="abstract-section container" aria-labelledby="abstract-title">
      <div class="abstract-grid">
        <h2 id="abstract-title">Abstract</h2>
        <p class="abstract-copy">{abstract}</p>
      </div>
    </section>
    <section id="results" class="results-section" aria-labelledby="results-title">
      <div class="container">
        <h2 id="results-title">Results</h2>
        <p class="section-intro">Four models on open-domain QA (AmbigQA-HQ, AmbigQA) and Text-to-SQL (AMBROSIA).</p>
        <article class="result-card" aria-labelledby="recovery-title">
          <div class="table-heading">
            <h3 id="recovery-title">Recovering model-realizable answers</h3>
            <p class="metric-note">Set F1 (%) · higher is better · bold: best per dataset and model</p>
          </div>
          <p class="table-mobile-hint">Swipe the table to see all models →</p>
          <div class="table-scroll" role="region" aria-label="Answer-set recovery results; scroll horizontally on a small screen" tabindex="0">
            <table class="results-table">
              <caption class="visually-hidden">Mean per-question set F1 for answer-set recovery on three datasets and four models.</caption>
              {header}
              {simple_table}
            </table>
          </div>
          <p class="result-takeaway"><strong>Highest set F1 in 7 of 12 settings.</strong> CircleClar exceeds both Sampling-50 and 1-Enumeration in all eight QA settings. The gap is largest for smaller models.</p>
          <details class="full-results">
            <summary>Full results with variability and exact match</summary>
            <p>Mean per-question set F1 ± population standard deviation; exact set match (EM) in percent. Standard deviations describe variability across questions.</p>
            <div class="table-scroll" role="region" aria-label="Full answer-set recovery results; scroll horizontally" tabindex="0">
              <table class="results-table">
                <caption>Set F1 ± standard deviation, with exact set match below each value.</caption>
                {header}
                {full_table}
              </table>
            </div>
          </details>
          <p class="paper-results-link">See <a href="assets/paper/circleclar.pdf" target="_blank" rel="noopener">the paper</a> for experimental setup and consistency-filtering analysis.</p>
        </article>
        <div class="downstream-grid">
          <article class="result-card" aria-labelledby="detection-title">
            <h3 id="detection-title">Detecting model-dependent ambiguity</h3>
            <p class="chart-note">AUROC (%) · 50 is chance · bold: best per row</p>
            <figure class="result-figure">
              {figure('heapmaptable', 'Model-dependent ambiguity detection', 'AUROC heatmap on AmbigQA-HQ and AmbigQA comparing CircleClar, ICE, CLARA-D, INTENT-SIM, and APA. CircleClar has the highest AUROC in all four HQ settings and two of four AmbigQA settings.', 1800, 1466)}
            </figure>
            <p class="result-caption"><strong>Model-specific ambiguity.</strong> The recovered set size provides an ambiguity score. CircleClar leads in six of eight QA settings; ICE leads on two AmbigQA models.</p>
          </article>
          <article class="result-card" aria-labelledby="policy-title">
            <h3 id="policy-title">Answer, clarify, or abstain?</h3>
            <p class="chart-note">Balanced accuracy (%) · error bars: 95% bootstrap CIs · dashed line: constant policy</p>
            <figure class="result-figure">
              {figure('policy', 'Answer, clarify, or abstain', 'Balanced accuracy of three-way response selection for four models on two QA datasets. CircleClar is compared with direct model-dependent and generic decision prompts, with 95% bootstrap confidence intervals and a constant-policy baseline.', 1800, 1408)}
            </figure>
            <p class="result-caption"><strong>From estimates to decisions.</strong> Empty estimated set: abstain. One answer: answer. Several: clarify. This policy leads in most evaluated QA settings.</p>
          </article>
        </div>
      </div>
    </section>
    <section id="bibtex" class="citation-section" aria-labelledby="bibtex-title">
      <div class="container">
        <h2 id="bibtex-title">BibTeX</h2>
        <div class="citation-box">
          <div class="citation-actions">
            <span id="copy-status" class="copy-status" role="status" aria-live="polite"></span>
            <button id="copy-bibtex" class="copy-button" type="button">{icon('copy')} Copy BibTeX</button>
          </div>
          <pre><code id="bibtex-entry">{escape(bibtex)}</code></pre>
        </div>
        <footer class="site-footer">Technical University of Munich · 2026</footer>
      </div>
    </section>
  </main>
  <dialog id="figure-dialog" class="lightbox" aria-labelledby="figure-dialog-title">
    <div class="lightbox-heading">
      <h2 id="figure-dialog-title" class="lightbox-title">Figure</h2>
      <button class="icon-button" type="button" data-close-dialog aria-label="Close enlarged figure">{icon('x')}</button>
    </div>
    <div class="lightbox-scroll" tabindex="0" aria-label="Enlarged figure; scroll to view details">
      <img class="lightbox-image" alt="">
    </div>
    <div class="lightbox-footer">
      <p>Scroll to inspect the figure. Press Escape to close.</p>
      <a id="figure-original" target="_blank" rel="noopener">Open original PDF</a>
    </div>
  </dialog>
</body>
</html>
'''

(SITE / 'index.html').write_text(document)
print('Generated', SITE / 'index.html')
print('48 source table cells, 7 CircleClar F1 wins; abstract copied from active paper text.')
