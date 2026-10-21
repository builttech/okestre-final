const statusEl = document.getElementById('status');
const openBtn = document.getElementById('openSidePanel');

openBtn?.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!chrome.sidePanel?.open || !tab?.windowId) {
    if (statusEl) statusEl.textContent = 'Side Panel indisponível neste navegador.';
    return;
  }
  await chrome.sidePanel.open({ windowId: tab.windowId });
  window.close();
});
