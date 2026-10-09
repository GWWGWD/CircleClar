const dialog = document.querySelector('#figure-dialog');
const dialogImage = dialog.querySelector('img');
const dialogTitle = dialog.querySelector('#figure-dialog-title');
const originalLink = dialog.querySelector('#figure-original');

document.querySelectorAll('[data-figure]').forEach(link => {
  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    dialogTitle.textContent = link.dataset.title;
    dialogImage.src = link.href;
    dialogImage.alt = link.dataset.alt ?? link.querySelector('img').alt;
    originalLink.href = link.dataset.original;
    dialog.showModal();
  });
});

dialog.querySelector('[data-close-dialog]').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});

const copyButton = document.querySelector('#copy-bibtex');
const copyStatus = document.querySelector('#copy-status');
let statusTimer;
copyButton.addEventListener('click', async () => {
  clearTimeout(statusTimer);
  try {
    await navigator.clipboard.writeText(document.querySelector('#bibtex-entry').textContent.trim());
    copyStatus.textContent = 'Copied to clipboard';
  } catch {
    const range = document.createRange();
    range.selectNodeContents(document.querySelector('#bibtex-entry'));
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    copyStatus.textContent = 'Text selected — copy with Ctrl/Cmd+C';
  }
  statusTimer = setTimeout(() => { copyStatus.textContent = ''; }, 4000);
});

const navLinks = [...document.querySelectorAll('.site-nav a')];
const sections = navLinks.map(link => document.querySelector(link.hash));
let updateScheduled = false;
function updateCurrentSection() {
  updateScheduled = false;
  const readingLine = Math.min(window.innerHeight * .35, 250);
  let current = sections[0];
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= readingLine) current = section;
  }
  if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) current = sections[sections.length - 1];
  navLinks.forEach(link => {
    if (link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
window.addEventListener('scroll', () => {
  if (!updateScheduled) {
    updateScheduled = true;
    requestAnimationFrame(updateCurrentSection);
  }
}, {passive: true});
updateCurrentSection();

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function setPlayButton(button, label, icon) {
  button.querySelector('span').textContent = label;
  button.querySelector('svg').innerHTML = icon === 'pause'
    ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
    : '<polygon points="6 4 20 12 6 20 6 4"/>';
}

// Starts a demo the first time it scrolls into view, unless the reader prefers reduced motion.
function autoplayOnce(element, start) {
  const observer = new IntersectionObserver(entries => {
    if (reducedMotion.matches || !entries.some(entry => entry.isIntersecting)) return;
    observer.disconnect();
    setTimeout(start, 600);
  }, {threshold: .3});
  observer.observe(element);
}

const tabs = [...document.querySelectorAll('.explorer-tab')];
function selectTab(tab) {
  tabs.forEach(other => {
    const selected = other === tab;
    other.setAttribute('aria-selected', selected);
    other.tabIndex = selected ? 0 : -1;
    document.getElementById(other.getAttribute('aria-controls')).hidden = !selected;
  });
}
tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectTab(tab));
  tab.addEventListener('keydown', event => {
    const offset = {ArrowRight: 1, ArrowLeft: -1}[event.key];
    if (!offset) return;
    const next = tabs[(index + offset + tabs.length) % tabs.length];
    selectTab(next);
    next.focus();
  });
});

const bijection = document.querySelector('[data-bijection]');
if (bijection) {
  // Illustrative rewrites of the running example; `fail` names the first desideratum each one violates.
  const CANDIDATES = [
    {text: 'Who voiced the snake in the Jungle Book movie?', fail: 'D1', why: 'fits both 1967 and 2016'},
    {text: 'Who voiced the snake in the 1967 animated film?', y: 1},
    {text: 'Who voiced Mowgli in the 1967 animated film?', fail: 'D2', answer: 'Bruce Reitherman'},
    {text: 'Which actress voiced the snake in the 2016 Jungle Book?', y: 2},
    {text: 'Who voiced Kaa in Disney’s 1967 animated The Jungle Book?', y: 1},
    {text: 'Who voiced a character in The Jungle Book?', fail: 'D1', why: 'dozens of possible answers'},
    {text: 'Who voiced Kaa in the 2016 live-action film?', y: 2},
    {text: 'Who directed the 2016 Jungle Book film?', fail: 'D2', answer: 'Jon Favreau'},
    {text: 'Who voiced Kaa in the 2010 series, seasons 1–2?', y: 3},
  ];
  const ANSWERS = {1: 'Holloway', 2: 'Johansson', 3: 'Terry'};
  const STEPS = [
    {rule: '<i>x</i> admits three valid answers', text: 'Nine rewrites of <i>x</i> that a model might propose. Which of them are valid clarifications? Switch on the desiderata one at a time, or press Play.'},
    {rule: 'D1 · Uniqueness — ∃ <i>y<sub>c</sub></i> : <i>p</i>*(<i>y<sub>c</sub></i> | <i>c</i>) = 1', text: 'A clarification must determine a single answer. Two rewrites still leave several answers open, so they do not resolve the ambiguity.'},
    {rule: 'D2 · Faithfulness — <i>y<sub>c</sub></i> ∈ <i>W</i>(<i>x</i>)', text: 'Its answer must also answer the original question. Asking about Mowgli or the director is unambiguous, but no longer about the snake. Six clarifications remain, mapping many-to-one onto three answers: not yet invertible.'},
    {rule: 'D3 · Answer equivalence — <i>c</i> ∼<sub><i>x</i></sub> <i>c</i>′ ⇔ <i>y<sub>c</sub></i> = <i>y<sub>c′</sub></i>', text: 'Clarifications with the same answer form one class. Each class now identifies exactly one answer and every answer exactly one class: the bijection of Proposition 4.1. Hover or tap a row to follow it.'},
  ];

  const stage = bijection.querySelector('.bij-stage');
  const pool = bijection.querySelector('[data-pool]');
  const poolHead = bijection.querySelector('[data-pool-head]');
  const links = bijection.querySelector('[data-links]');
  const stepButtons = [...bijection.querySelectorAll('[data-step-to]')];
  const playButton = bijection.querySelector('[data-play]');
  const rows = [...bijection.querySelectorAll('.bij-row')];
  const classLists = Object.fromEntries(rows.map(row => [row.dataset.row, row.querySelector('[data-class]')]));
  const answers = Object.fromEntries(rows.map(row => [row.dataset.row, row.querySelector('.bij-answer')]));

  const chips = CANDIDATES.map(candidate => {
    const el = document.createElement('li');
    el.className = 'chip';
    el.innerHTML = '<span class="chip-text"></span><span class="chip-tag"></span>';
    el.querySelector('.chip-text').textContent = candidate.text;
    pool.append(el);
    return {...candidate, el, tag: el.querySelector('.chip-tag')};
  });
  const movable = [...chips.map(chip => chip.el), ...Object.values(answers)];

  let step = 0;

  function chipState(chip) {
    if (step >= 1 && chip.fail === 'D1') return {rejected: true, tag: `✗ ${chip.why}`};
    if (step >= 2 && chip.fail === 'D2') return {rejected: true, tag: `✗ ${chip.answer} ∉ W(x)`};
    if (step >= 1) return {rejected: false, tag: `→ ${chip.answer ?? ANSWERS[chip.y]}`};
    return {rejected: false, tag: ''};
  }

  function curve(from, to, stageBox) {
    const x1 = from.right - stageBox.left + 4, y1 = from.top + from.height / 2 - stageBox.top;
    const x2 = to.left - stageBox.left - 4, y2 = to.top + to.height / 2 - stageBox.top;
    const mid = (x1 + x2) / 2;
    return `M${x1} ${y1}C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}`;
  }

  function drawLinks(animate) {
    const stageBox = stage.getBoundingClientRect();
    const paths = [];
    if (step === 2) {
      chips.filter(chip => chip.y).forEach(chip => paths.push({row: chip.y, d: curve(chip.el.getBoundingClientRect(), answers[chip.y].getBoundingClientRect(), stageBox)}));
    } else if (step === 3) {
      rows.forEach(row => paths.push({row: row.dataset.row, bi: true, d: curve(row.querySelector('.bij-class').getBoundingClientRect(), answers[row.dataset.row].getBoundingClientRect(), stageBox)}));
    }
    const focus = stage.dataset.focus;
    links.innerHTML = paths.map((path, index) => {
      const marker = path.bi ? 'url(#bij-arrow-green)' : 'url(#bij-arrow)';
      const classes = [path.bi && 'bi', animate && 'draw', String(path.row) === focus && 'focus'].filter(Boolean).join(' ');
      return `<path d="${path.d}" pathLength="1" data-row="${path.row}" class="${classes}" style="--d:${.5 + index * .07}s" marker-end="${marker}"${path.bi ? ` marker-start="${marker}"` : ''}/>`;
    }).join('');
  }

  function render(animate) {
    animate = animate && !reducedMotion.matches;
    const before = new Map(movable.map(el => [el, el.getBoundingClientRect()]));
    bijection.dataset.step = step;
    stepButtons.forEach((button, index) => {
      button.setAttribute('aria-pressed', index === step);
      button.classList.toggle('done', index < step);
    });
    bijection.querySelector('[data-rule]').innerHTML = STEPS[step].rule;
    bijection.querySelector('[data-text]').innerHTML = STEPS[step].text;
    poolHead.textContent = step >= 2 ? 'Rejected — not valid clarifications' : 'Candidate rewrites of x';
    chips.forEach(chip => {
      const state = chipState(chip);
      const newlyRejected = state.rejected && !chip.el.classList.contains('rejected');
      chip.el.classList.toggle('rejected', state.rejected);
      chip.tag.textContent = state.tag;
      (step >= 2 && chip.y ? classLists[chip.y] : pool).append(chip.el);
      if (newlyRejected && animate) {
        chip.el.classList.remove('shake');
        void chip.el.offsetWidth;
        chip.el.classList.add('shake');
      }
    });
    drawLinks(animate);
    if (!animate) return;
    movable.forEach(el => {
      const first = before.get(el), last = el.getBoundingClientRect();
      const dx = first.left - last.left, dy = first.top - last.top;
      if (!dx && !dy) return;
      el.animate([{transform: `translate(${dx}px, ${dy}px)`}, {transform: 'none'}], {duration: 650, easing: 'cubic-bezier(.2, .7, .2, 1)'});
    });
  }

  let timer = null;
  const setPlayLabel = (label, icon) => setPlayButton(playButton, label, icon);
  function stop() {
    clearInterval(timer);
    timer = null;
    setPlayLabel(step === 3 ? 'Replay' : 'Play');
  }
  function play() {
    if (step === 3) { step = 0; render(true); }
    setPlayLabel('Pause', 'pause');
    timer = setInterval(() => {
      step += 1;
      render(true);
      if (step === 3) stop();
    }, 2600);
  }

  stepButtons.forEach((button, index) => button.addEventListener('click', () => {
    stop();
    if (index === step) return;
    step = index;
    render(true);
    setPlayLabel(step === 3 ? 'Replay' : 'Play');
  }));
  playButton.addEventListener('click', () => (timer ? stop() : play()));

  rows.forEach(row => {
    const focus = () => {
      stage.dataset.focus = row.dataset.row;
      rows.forEach(other => other.classList.toggle('focus', other === row));
      links.querySelectorAll('path').forEach(path => path.classList.toggle('focus', path.dataset.row === row.dataset.row));
    };
    const blur = () => {
      delete stage.dataset.focus;
      row.classList.remove('focus');
      links.querySelectorAll('path').forEach(path => path.classList.remove('focus'));
    };
    row.addEventListener('mouseenter', focus);
    row.addEventListener('mouseleave', blur);
    row.addEventListener('click', () => (row.classList.contains('focus') ? blur() : focus()));
  });

  // Redraw only when the width changes: height changes come from render(), whose FLIP transforms would skew the measurements.
  let stageWidth = 0;
  new ResizeObserver(([entry]) => {
    if (entry.contentRect.width === stageWidth) return;
    stageWidth = entry.contentRect.width;
    drawLinks(false);
  }).observe(stage);

  autoplayOnce(bijection, play);

  render(false);
}

const worldModel = document.querySelector('[data-world-model]');
if (worldModel) {
  // Illustrative models; the paper's running example contrasts a model that knows both films with one that knows only 2016.
  const MODELS = [
    {knows: [1, 2], who: 'knows both Jungle Book films', text: 'Model A realizes two of the three interpretations. Answering with a single name would silently commit to one film, so it should ask which one is meant.'},
    {knows: [2], who: 'knows only the 2016 film', text: 'The question is just as ambiguous in the world, but from Model B’s perspective there is no alternative interpretation to act on. It should simply answer.'},
    {knows: [1, 2, 3], who: 'knows all three adaptations', text: 'Only for a model that realizes every valid answer does model ambiguity coincide with world ambiguity.'},
    {knows: [], who: 'knows none of the adaptations', text: 'Model D cannot produce any valid answer. Anything it says would be a guess, so it should abstain.'},
  ];
  const CLARIFIED = {1: 'Who voiced Kaa in the 1967 animated film?', 2: 'Who voiced Kaa in the 2016 live-action film?', 3: 'Who voiced Kaa in the 2010 animated series?'};
  const RESPONSES = [['Abstain', 'abstain'], ['Answer', 'answer'], ['Clarify', 'clarify']];

  const world = worldModel.querySelector('.wm-world');
  const region = worldModel.querySelector('[data-region]');
  const modelButtons = [...worldModel.querySelectorAll('[data-model]')];
  const answerCards = [...worldModel.querySelectorAll('[data-answer]')];
  const detail = worldModel.querySelector('[data-detail]');
  const sizeOut = worldModel.querySelector('[data-model-size]');
  const responseOut = worldModel.querySelector('[data-response]');
  const playButton = worldModel.querySelector('[data-play]');
  const defaultDetail = 'Hover or tap an answer to see the interpretation behind it.';
  let current = 0;
  let activeAnswer = null;

  function placeRegion() {
    const known = answerCards.filter(card => card.classList.contains('known'));
    const box = world.getBoundingClientRect();
    if (!known.length) {
      Object.assign(region.style, {left: `${box.width / 2}px`, top: `${box.height / 2}px`, width: '0px', height: '0px', opacity: 0});
      return;
    }
    const rects = known.map(card => card.getBoundingClientRect());
    const left = Math.min(...rects.map(r => r.left)) - box.left - 12;
    const top = Math.min(...rects.map(r => r.top)) - box.top - 12;
    const right = Math.max(...rects.map(r => r.right)) - box.left + 12;
    const bottom = Math.max(...rects.map(r => r.bottom)) - box.top + 24;
    Object.assign(region.style, {left: `${left}px`, top: `${top}px`, width: `${right - left}px`, height: `${bottom - top}px`, opacity: 1});
  }

  function showDetail(card) {
    activeAnswer = card;
    answerCards.forEach(other => other.classList.toggle('active', other === card));
    if (!card) { detail.textContent = defaultDetail; return; }
    const id = Number(card.dataset.answer);
    const name = card.querySelector('strong').textContent;
    const model = `Model ${'ABCD'[current]}`;
    detail.innerHTML = `Interpretation: <q>${CLARIFIED[id]}</q> → ${name}. ` + (MODELS[current].knows.includes(id)
      ? `<strong>${model} can produce this answer.</strong>`
      : `<strong>${model} does not know it</strong>, so this interpretation is invisible to it.`);
  }

  function render(animate) {
    const model = MODELS[current];
    const name = `Model ${'ABCD'[current]}`;
    modelButtons.forEach((button, index) => button.setAttribute('aria-pressed', index === current));
    worldModel.querySelector('[data-rule]').textContent = `${name} · ${model.who}`;
    worldModel.querySelector('[data-text]').textContent = model.text;
    answerCards.forEach(card => {
      const known = model.knows.includes(Number(card.dataset.answer));
      card.classList.toggle('known', known);
      card.querySelector('.wm-status').textContent = known ? `✓ realizable by ${name}` : `✗ unknown to ${name}`;
    });
    region.querySelector('[data-region-label]').innerHTML = `<i>M</i>(<i>x</i>) · ${name}`;
    const [label, kind] = RESPONSES[Math.min(model.knows.length, 2)];
    sizeOut.innerHTML = `|<i>M</i>(<i>x</i>)| = ${model.knows.length}`;
    responseOut.textContent = label;
    responseOut.className = `response-${kind}`;
    if (animate && !reducedMotion.matches) {
      [sizeOut, responseOut].forEach(out => { out.classList.remove('pop'); void out.offsetWidth; out.classList.add('pop'); });
    }
    showDetail(activeAnswer);
    placeRegion();
  }

  let timer = null;
  function stop() {
    clearInterval(timer);
    timer = null;
    setPlayButton(playButton, 'Play');
  }
  function play() {
    setPlayButton(playButton, 'Pause', 'pause');
    timer = setInterval(() => {
      current = (current + 1) % MODELS.length;
      render(true);
      if (current === 0) stop();
    }, 2600);
  }
  playButton.addEventListener('click', () => (timer ? stop() : play()));
  modelButtons.forEach((button, index) => button.addEventListener('click', () => {
    stop();
    current = index;
    render(true);
  }));
  answerCards.forEach(card => {
    card.addEventListener('mouseenter', () => showDetail(card));
    card.addEventListener('focus', () => showDetail(card));
    card.addEventListener('click', () => showDetail(card));
    card.addEventListener('mouseleave', () => showDetail(null));
    card.addEventListener('blur', () => showDetail(null));
  });
  new ResizeObserver(placeRegion).observe(world);
  autoplayOnce(worldModel, play);
  render(false);
}

const circleClar = document.querySelector('[data-circleclar]');
if (circleClar) {
  // One illustrative run with the repository defaults (B = 6 enumeration samples, R = 10 re-answers, τ = 0.6).
  const SAMPLES = [
    ['Scarlett Johansson', 'Sterling Holloway'],
    ['Scarlett Johansson'],
    ['Sterling Holloway', 'Scarlett Johansson', 'Neel Sethi'],
    ['Scarlett Johansson', 'Joseph J. Terry'],
    ['Sterling Holloway'],
    ['Scarlett Johansson', 'Neel Sethi'],
  ];
  const CANDIDATES = [
    {name: 'Scarlett Johansson', clarification: 'Who voiced Kaa in the 2016 live-action The Jungle Book?', answers: {'Scarlett Johansson': 10}},
    {name: 'Sterling Holloway', clarification: 'Who voiced Kaa in Disney’s 1967 animated The Jungle Book?', answers: {'Sterling Holloway': 8, 'Sebastian Cabot': 2}},
    {name: 'Neel Sethi', clarification: 'Who voiced the snake in the 2016 Jungle Book film?', answers: {'Scarlett Johansson': 7, 'Neel Sethi': 3}, note: 'Neel Sethi played Mowgli, so no snake interpretation leads back to him.'},
    {name: 'Joseph J. Terry', clarification: 'Who voiced Kaa in the 2010 animated series, seasons 1–2?', answers: {'Joseph J. Terry': 6, 'Jim Cummings': 2, 'Sterling Holloway': 2}},
  ];
  const R = 10;
  const ORDER = [3, 7, 0, 9, 1, 5, 8, 2, 6, 4];
  CANDIDATES.forEach(candidate => {
    const counts = Object.entries(candidate.answers).sort((a, b) => b[1] - a[1]);
    candidate.hits = candidate.answers[candidate.name] ?? 0;
    candidate.q = candidate.hits / R;
    candidate.mostFrequent = counts[0][0] === candidate.name && (counts.length === 1 || counts[1][1] < counts[0][1]);
    const outcomes = counts.flatMap(([answer, count]) => Array(count).fill(answer));
    candidate.dots = ORDER.map(index => outcomes[index]);
  });

  const FRAMES = [{phase: 'idle'}, {phase: 'enumerate'}];
  CANDIDATES.forEach((_, i) => ['clarify', 'reanswer', 'verdict'].forEach(phase => FRAMES.push({phase, i})));
  FRAMES.push({phase: 'done'});

  const $ = selector => circleClar.querySelector(selector);
  const tauInput = $('[data-tau]');
  const playButton = $('[data-play]');
  const nextButton = $('[data-next]');
  let frame = 0;
  let selected = null;
  let typing = null;

  const tau = () => Number(tauInput.value);
  const accepted = candidate => candidate.mostFrequent && candidate.q >= tau() - 1e-9;
  const qText = candidate => candidate.q.toFixed(1);

  function evaluatedCount(f) {
    if (f.phase === 'done') return CANDIDATES.length;
    if (f.i === undefined) return 0;
    return f.phase === 'verdict' ? f.i + 1 : f.i;
  }

  function verdictText(candidate) {
    if (!candidate.mostFrequent) return `✗ ${candidate.name} is not the most frequent answer to its own clarification (q̂ = ${qText(candidate)}), so the cycle does not close.`;
    if (!accepted(candidate)) return `✗ q̂ = ${qText(candidate)} < τ = ${tau()}: the model does not recover ${candidate.name} reliably enough.`;
    return `✓ q̂ = ${qText(candidate)} ≥ τ = ${tau()} and ${candidate.name} is the most frequent answer: the cycle closes.`;
  }

  function explain(f) {
    const c = CANDIDATES[f.i];
    switch (f.phase) {
      case 'idle': return ['CircleClar · B = 6, R = 10, τ = 0.6', 'Press Play to watch one run, or Step through it yourself.'];
      case 'enumerate': return ['Step 1 · Propose candidates', 'The model is asked six times for all plausible answers to x. The union of its answers, grouped by meaning, gives four candidates. Not all of them have to be valid.'];
      case 'clarify': return ['Step 2 · Answer → clarification', `For ỹ = ${c.name}, the same model writes a clarification of x that should make this the unique answer.`];
      case 'reanswer': return ['Step 3 · Clarification → answer', `The model answers this clarification ten times independently. If it really expresses ${c.name}’s interpretation, the answers should come back to ${c.name}.`];
      case 'verdict': return ['Step 4 · Recovery check', `q̂ is the share of re-answers that return to ỹ. A candidate is kept only if it is the unique most frequent answer and q̂ ≥ τ.${c.note ? ` ${c.note}` : ''}`];
      default: {
        const kept = CANDIDATES.filter(accepted).map(candidate => candidate.name);
        return ['Result', `At τ = ${tau()}, CircleClar estimates M̂(x) = {${kept.join(', ')}}. Drag τ to see which answers the model recovers reliably, or pick a candidate to review its cycle.`];
      }
    }
  }

  function render(animate) {
    animate = animate && !reducedMotion.matches;
    clearInterval(typing);
    const f = FRAMES[frame];
    const evaluated = evaluatedCount(f);
    const view = f.phase === 'done' ? (selected ?? CANDIDATES.length - 1) : f.i;
    const candidate = CANDIDATES[view];
    circleClar.dataset.phase = f.phase;

    const [rule, text] = explain(f);
    $('[data-rule]').textContent = rule;
    $('[data-text]').textContent = text;
    $('[data-tau-value]').textContent = tau().toFixed(1);
    nextButton.disabled = f.phase === 'done';

    const entering = animate && f.phase === 'enumerate';
    $('[data-samples]').innerHTML = frame >= 1
      ? SAMPLES.map((answers, i) => `<li data-n="${i + 1}"${entering ? ` class="enter" style="--d:${i * .12}s"` : ''}>${answers.join(', ')}</li>`).join('')
      : '';
    $('[data-candidates]').innerHTML = frame >= 1
      ? CANDIDATES.map((c, i) => {
        const done = i < evaluated;
        const status = done ? (accepted(c) ? 'accepted' : 'rejected') : '';
        const badge = done ? `q̂ ${qText(c)} ${accepted(c) ? '✓' : '✗'}` : '';
        const classes = [status, i === view && f.phase !== 'enumerate' && 'current', entering && 'enter'].filter(Boolean).join(' ');
        return `<li class="${classes}" style="--d:${.8 + i * .15}s"${done && f.phase === 'done' ? ` data-pick="${i}" tabindex="0" role="button"` : ''}><span>${c.name}</span><span class="cc-badge">${badge}</span></li>`;
      }).join('')
      : '';
    $('[data-estimate]').innerHTML = CANDIDATES.slice(0, evaluated).filter(accepted)
      .map(c => `<li${animate && f.phase === 'verdict' && c === candidate ? ' class="enter"' : ''}>${c.name}</li>`).join('');

    const showCycle = candidate && f.phase !== 'enumerate';
    $('[data-candidate]').textContent = showCycle ? candidate.name : '—';
    const clarification = $('[data-clarification]');
    if (showCycle && animate && f.phase === 'clarify') {
      let shown = 0;
      clarification.textContent = '';
      typing = setInterval(() => {
        shown += 1;
        clarification.textContent = candidate.clarification.slice(0, shown);
        if (shown >= candidate.clarification.length) clearInterval(typing);
      }, 22);
    } else {
      clarification.textContent = showCycle ? candidate.clarification : '—';
    }

    const answered = showCycle && f.phase !== 'clarify';
    $('[data-dots]').innerHTML = answered
      ? candidate.dots.map((answer, i) => `<span class="cc-dot${answer === candidate.name ? ' hit' : ''}" title="${answer}"${animate && f.phase === 'reanswer' ? ` style="--d:${.6 + i * .12}s"` : ' style="animation:none"'}></span>`).join('')
      : '';
    $('[data-tally]').innerHTML = answered
      ? Object.entries(candidate.answers).map(([answer, count]) => answer === candidate.name ? `<b>${answer} ×${count}</b>` : `${answer} ×${count}`).join(' · ')
      : '';
    const judged = showCycle && (f.phase === 'verdict' || f.phase === 'done');
    const fill = $('[data-fill]');
    fill.style.width = judged ? `${candidate.q * 100}%` : '0';
    fill.className = `cc-fill${judged ? (accepted(candidate) ? ' pass' : ' fail') : ''}`;
    $('[data-threshold]').style.left = `${tau() * 100}%`;
    const verdict = $('[data-verdict]');
    verdict.textContent = judged ? verdictText(candidate) : '';
    verdict.className = `cc-verdict${judged ? (accepted(candidate) ? ' pass' : ' fail') : ''}`;
  }

  let timer = null;
  function stop() {
    clearInterval(timer);
    timer = null;
    setPlayButton(playButton, frame === FRAMES.length - 1 ? 'Replay' : 'Play');
  }
  function advance() {
    frame += 1;
    selected = null;
    render(true);
    if (frame === FRAMES.length - 1) stop();
  }
  function play() {
    if (frame === FRAMES.length - 1) { frame = 0; render(false); }
    setPlayButton(playButton, 'Pause', 'pause');
    advance();
    timer = setInterval(advance, 2400);
  }
  playButton.addEventListener('click', () => (timer ? stop() : play()));
  nextButton.addEventListener('click', () => { stop(); advance(); });
  $('[data-reset]').addEventListener('click', () => { stop(); frame = 0; selected = null; render(false); setPlayButton(playButton, 'Play'); });
  tauInput.addEventListener('input', () => render(false));
  const pick = event => {
    const item = event.target.closest('[data-pick]');
    if (!item || (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ')) return;
    event.preventDefault();
    selected = Number(item.dataset.pick);
    render(false);
    circleClar.querySelector(`[data-pick="${selected}"]`).focus();
  };
  $('[data-candidates]').addEventListener('click', pick);
  $('[data-candidates]').addEventListener('keydown', pick);
  autoplayOnce(circleClar, play);
  render(false);
}

// Links from the results back to a demo open the matching tab before scrolling to it.
document.querySelectorAll('[data-open-tab]').forEach(link => {
  link.addEventListener('click', () => selectTab(document.getElementById(link.dataset.openTab)));
});
