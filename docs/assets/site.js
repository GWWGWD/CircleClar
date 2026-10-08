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
    dialogImage.alt = link.querySelector('img').alt;
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
