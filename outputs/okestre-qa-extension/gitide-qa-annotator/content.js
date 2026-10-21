function gitideQaSelectorFor(element) {
  if (!element || element.nodeType !== Node.ELEMENT_NODE) return '';
  if (element.id) return `#${CSS.escape(element.id)}`;
  const parts = [];
  let current = element;
  while (current && current.nodeType === Node.ELEMENT_NODE && parts.length < 5) {
    let part = current.tagName.toLowerCase();
    const testId = current.getAttribute('data-testid') || current.getAttribute('data-test');
    if (testId) {
      part += `[data-testid="${CSS.escape(testId)}"]`;
      parts.unshift(part);
      break;
    }
    const className = Array.from(current.classList || []).filter(Boolean).slice(0, 2).map(cls => `.${CSS.escape(cls)}`).join('');
    if (className) part += className;
    const parent = current.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children).filter(child => child.tagName === current.tagName);
      if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(current) + 1})`;
    }
    parts.unshift(part);
    current = parent;
  }
  return parts.join(' > ');
}

let gitideQaEvidenceMarker = null;

function gitideQaRemoveEvidenceMarker() {
  if (gitideQaEvidenceMarker) {
    gitideQaEvidenceMarker.remove();
    gitideQaEvidenceMarker = null;
  }
}

function gitideQaShowEvidenceMarker(rect) {
  gitideQaRemoveEvidenceMarker();
  if (!rect || !Number.isFinite(rect.x) || !Number.isFinite(rect.y)) return;
  const marker = document.createElement('div');
  marker.setAttribute('data-gitide-qa-evidence', 'true');
  marker.style.cssText = [
    'position:fixed',
    `left:${rect.x}px`,
    `top:${rect.y}px`,
    `width:${Math.max(rect.width, 8)}px`,
    `height:${Math.max(rect.height, 8)}px`,
    'z-index:2147483647',
    'pointer-events:none',
    'border:3px solid #ff4f7b',
    'background:rgba(255,79,123,0.16)',
    'border-radius:8px',
    'box-shadow:0 0 0 9999px rgba(0,0,0,0.10), 0 0 0 6px rgba(255,79,123,0.18)'
  ].join(';');
  document.documentElement.appendChild(marker);
  gitideQaEvidenceMarker = marker;
}

function gitideQaStartPicker(sendResponse) {
  const previousCursor = document.body.style.cursor;
  let highlighted = null;

  const overlay = document.createElement('div');
  overlay.style.cssText = [
    'position:fixed',
    'inset:0',
    'z-index:2147483647',
    'pointer-events:none',
    'background:rgba(255,255,255,0.01)'
  ].join(';');
  document.documentElement.appendChild(overlay);
  document.body.style.cursor = 'crosshair';

  const highlight = document.createElement('div');
  highlight.style.cssText = [
    'position:fixed',
    'z-index:2147483647',
    'border:2px solid #ff6b8a',
    'background:rgba(255,107,138,0.12)',
    'pointer-events:none',
    'border-radius:6px',
    'box-shadow:0 0 0 9999px rgba(0,0,0,0.12)'
  ].join(';');
  document.documentElement.appendChild(highlight);

  const move = (event) => {
    highlighted = event.target;
    const rect = highlighted.getBoundingClientRect();
    highlight.style.left = `${rect.left}px`;
    highlight.style.top = `${rect.top}px`;
    highlight.style.width = `${rect.width}px`;
    highlight.style.height = `${rect.height}px`;
  };

  const cleanup = () => {
    document.body.style.cursor = previousCursor;
    document.removeEventListener('mousemove', move, true);
    document.removeEventListener('click', pick, true);
    document.removeEventListener('keydown', cancel, true);
    overlay.remove();
    highlight.remove();
  };

  const pick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const target = highlighted || event.target;
    const rect = target.getBoundingClientRect();
    cleanup();
    sendResponse({
      ok: true,
      selector: gitideQaSelectorFor(target),
      text: (target.innerText || target.textContent || '').trim().slice(0, 240),
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }
    });
  };

  const cancel = (event) => {
    if (event.key !== 'Escape') return;
    cleanup();
    sendResponse({ ok: false, reason: 'cancelled' });
  };

  document.addEventListener('mousemove', move, true);
  document.addEventListener('click', pick, true);
  document.addEventListener('keydown', cancel, true);
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === 'GITIDE_QA_PICK_ELEMENT') {
    gitideQaStartPicker(sendResponse);
    return true;
  }
  if (message?.type === 'GITIDE_QA_SHOW_EVIDENCE_MARKER') {
    gitideQaShowEvidenceMarker(message.rect);
    sendResponse({ ok: true });
    return false;
  }
  if (message?.type === 'GITIDE_QA_CLEAR_EVIDENCE_MARKER') {
    gitideQaRemoveEvidenceMarker();
    sendResponse({ ok: true });
    return false;
  }
  return false;
});
