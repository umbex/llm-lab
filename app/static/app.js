const flags = {
  session: document.getElementById('flag-session'),
  system: document.getElementById('flag-system'),
  memory: document.getElementById('flag-memory'),
  kb: document.getElementById('flag-kb'),
};

const panels = {
  system: document.getElementById('system-panel'),
  memory: document.getElementById('memory-panel'),
  kb: document.getElementById('kb-panel'),
};

const inputs = {
  systemPrompt: document.getElementById('system-prompt'),
  memoryList: document.getElementById('memory-list'),
  kbFile: document.getElementById('kb-file'),
  kbStatus: document.getElementById('kb-status'),
  userInput: document.getElementById('user-input'),
};

const ui = {
  chatForm: document.getElementById('chat-form'),
  messages: document.getElementById('messages'),
  statusLine: document.getElementById('status-line'),
  thinkingIndicator: document.getElementById('thinking-indicator'),
  sendButton: document.getElementById('send-button'),
  clearChat: document.getElementById('clear-chat'),
  clearMemory: document.getElementById('clear-memory'),
  uploadKb: document.getElementById('upload-kb'),
};

const PROMPT_HISTORY_KEY = 'llm_lab_prompt_history_v1';
const MAX_PROMPT_HISTORY = 100;
let promptHistory = [];
let historyIndex = -1;

function generateSessionId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const sessionId = generateSessionId();

function togglePanels() {
  panels.system.classList.toggle('hidden', !flags.system.checked);
  panels.memory.classList.toggle('hidden', !flags.memory.checked);
  panels.kb.classList.toggle('hidden', !flags.kb.checked);
  updateStatusFromFlags();
}

function addMessage(role, content) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  if (role === 'assistant') {
    el.innerHTML = renderMarkdown(content);
  } else {
    el.textContent = content;
  }
  ui.messages.appendChild(el);
  ui.messages.scrollTop = ui.messages.scrollHeight;
}

function setThinking(isThinking) {
  inputs.userInput.disabled = isThinking;
  ui.sendButton.disabled = isThinking;
  ui.clearChat.disabled = isThinking;
  ui.chatForm.classList.toggle('processing', isThinking);
  ui.thinkingIndicator.classList.toggle('hidden', !isThinking);
}

function clearChatWindow() {
  ui.messages.innerHTML = '';
}

function updateStatusFromFlags() {
  ui.statusLine.textContent = 'Prompt Size (bytes): -';
}

function loadPromptHistory() {
  try {
    const raw = localStorage.getItem(PROMPT_HISTORY_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      promptHistory = parsed.filter((x) => typeof x === 'string' && x.trim()).slice(-MAX_PROMPT_HISTORY);
    }
  } catch {}
}

function persistPromptHistory() {
  localStorage.setItem(PROMPT_HISTORY_KEY, JSON.stringify(promptHistory.slice(-MAX_PROMPT_HISTORY)));
}

function savePromptToHistory(prompt) {
  const text = prompt.trim();
  if (!text) return;
  if (promptHistory[promptHistory.length - 1] !== text) {
    promptHistory.push(text);
    if (promptHistory.length > MAX_PROMPT_HISTORY) {
      promptHistory = promptHistory.slice(-MAX_PROMPT_HISTORY);
    }
    persistPromptHistory();
  }
  historyIndex = -1;
}

function showHistoryPrompt(step) {
  if (!promptHistory.length) return;
  if (historyIndex === -1) {
    historyIndex = promptHistory.length;
  }
  historyIndex += step;
  if (historyIndex < 0) historyIndex = 0;
  if (historyIndex > promptHistory.length) historyIndex = promptHistory.length;

  if (historyIndex === promptHistory.length) {
    inputs.userInput.value = '';
  } else {
    inputs.userInput.value = promptHistory[historyIndex];
  }
  inputs.userInput.focus();
}

function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderInlineMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/(^|[\s(])_(.+?)_(?=$|[\s).,!?:;])/g, '$1<em>$2</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
    );
}

function renderMarkdown(text) {
  const escaped = escapeHtml(text);
  const lines = escaped.split('\n');
  const html = [];
  let inCodeBlock = false;
  let inList = false;
  let inBlockquote = false;
  let blockquoteLines = [];
  let paragraphLines = [];

  const flushParagraph = () => {
    if (!paragraphLines.length) return;
    html.push(`<p>${renderInlineMarkdown(paragraphLines.join(' '))}</p>`);
    paragraphLines = [];
  };

  const flushBlockquote = () => {
    if (!blockquoteLines.length) return;
    html.push(`<blockquote>${renderInlineMarkdown(blockquoteLines.join(' '))}</blockquote>`);
    blockquoteLines = [];
  };

  for (const line of lines) {
    if (line.trim().startsWith('```')) {
      flushBlockquote();
      flushParagraph();
      if (!inCodeBlock) {
        if (inList) {
          html.push('</ul>');
          inList = false;
        }
        html.push('<pre><code>');
        inCodeBlock = true;
      } else {
        html.push('</code></pre>');
        inCodeBlock = false;
      }
      continue;
    }

    if (inCodeBlock) {
      html.push(`${line}\n`);
      continue;
    }

    const quoteMatch = line.match(/^\s*>+\s?(.*)$/);
    if (quoteMatch) {
      flushParagraph();
      if (inList) {
        html.push('</ul>');
        inList = false;
      }
      inBlockquote = true;
      blockquoteLines.push(quoteMatch[1].trim());
      continue;
    }

    const inlineQuoteMatch = line.match(/^(.+?)\s+>+\s?(.*)$/);
    if (inlineQuoteMatch && inlineQuoteMatch[2].trim()) {
      flushParagraph();
      if (inList) {
        html.push('</ul>');
        inList = false;
      }
      const prefix = inlineQuoteMatch[1].trim();
      if (prefix) {
        html.push(`<p>${renderInlineMarkdown(prefix)}</p>`);
      }
      inBlockquote = true;
      blockquoteLines.push(inlineQuoteMatch[2].trim());
      continue;
    }

    if (inBlockquote) {
      flushBlockquote();
      inBlockquote = false;
    }

    const bulletMatch = line.match(/^\s*[-*]\s+(.+)$/);
    if (bulletMatch) {
      flushParagraph();
      if (!inList) {
        html.push('<ul>');
        inList = true;
      }
      html.push(`<li>${renderInlineMarkdown(bulletMatch[1])}</li>`);
      continue;
    }

    if (inList) {
      html.push('</ul>');
      inList = false;
    }

    if (line.trim() === '') {
      flushBlockquote();
      inBlockquote = false;
      flushParagraph();
      continue;
    }

    if (line.startsWith('### ')) {
      flushParagraph();
      html.push(`<h3>${renderInlineMarkdown(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith('## ')) {
      flushParagraph();
      html.push(`<h2>${renderInlineMarkdown(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith('# ')) {
      flushParagraph();
      html.push(`<h1>${renderInlineMarkdown(line.slice(2))}</h1>`);
      continue;
    }

    paragraphLines.push(line.trim());
  }

  flushParagraph();
  flushBlockquote();
  if (inList) {
    html.push('</ul>');
  }
  if (inCodeBlock) {
    html.push('</code></pre>');
  }

  return html.join('');
}

async function refreshMemory() {
  const res = await fetch('/memory');
  const data = await res.json();
  const facts = data.facts || {};
  const entries = Object.entries(facts);
  if (!entries.length) {
    inputs.memoryList.innerHTML = '<div class="hint">No memory facts yet.</div>';
    return;
  }
  inputs.memoryList.innerHTML = entries
    .map(([key, value]) => `<div class="memory-item"><strong>${escapeHtml(key)}</strong>: ${escapeHtml(value)}</div>`)
    .join('');
}

function scheduleMemoryRefresh() {
  const delays = [400, 1200, 2500];
  for (const delay of delays) {
    setTimeout(() => {
      refreshMemory().catch(() => {});
    }, delay);
  }
}

async function clearMemory() {
  const res = await fetch('/memory', { method: 'DELETE' });
  inputs.kbStatus.textContent = res.ok ? 'Memory cleared.' : 'Memory clear failed.';
  await refreshMemory();
}

async function uploadKb() {
  const file = inputs.kbFile.files[0];
  if (!file) {
    inputs.kbStatus.textContent = 'Select a .md file first.';
    return;
  }
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/kb/upload', { method: 'POST', body: form });
  const data = await res.json();
  if (!res.ok) {
    inputs.kbStatus.textContent = data.detail || 'Upload failed';
    return;
  }
  inputs.kbStatus.textContent = `Uploaded and active: ${data.filename}`;
}

async function refreshKbStatus() {
  const res = await fetch('/kb');
  const data = await res.json();
  if (data.filename) {
    inputs.kbStatus.textContent = `Active KB: ${data.filename}`;
  }
}

async function sendChat(message) {
  const payload = {
    message,
    flags: {
      session: flags.session.checked,
      system: flags.system.checked,
      memory: flags.memory.checked,
      kb: flags.kb.checked,
    },
  };
  if (flags.session.checked) {
    payload.session_id = sessionId;
  }
  if (flags.system.checked && inputs.systemPrompt.value.trim()) {
    payload.system_prompt = inputs.systemPrompt.value;
  }

  try {
    setThinking(true);
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    let data;
    try {
      data = await res.json();
    } catch {
      data = { detail: 'non-JSON response from server' };
    }
    if (!res.ok) {
      addMessage('assistant', `Error: ${data.detail || 'request failed'}`);
      return;
    }

    addMessage('assistant', data.reply);
    ui.statusLine.textContent = `Prompt Size (bytes): ${data.prompt_bytes}`;
    scheduleMemoryRefresh();
  } catch (error) {
    addMessage('assistant', `Error: ${error.message || 'network error'}`);
  } finally {
    setThinking(false);
    inputs.userInput.focus();
  }
}

Object.values(flags).forEach((el) => el.addEventListener('change', togglePanels));
ui.clearMemory.addEventListener('click', clearMemory);
ui.uploadKb.addEventListener('click', uploadKb);
ui.clearChat.addEventListener('click', clearChatWindow);
ui.chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = inputs.userInput.value.trim();
  if (!text) return;
  savePromptToHistory(text);
  addMessage('user', text);
  inputs.userInput.value = '';
  await sendChat(text);
});
inputs.userInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    ui.chatForm.requestSubmit();
  }
  const atStart =
    inputs.userInput.selectionStart === 0 &&
    inputs.userInput.selectionEnd === 0;
  const atEnd =
    inputs.userInput.selectionStart === inputs.userInput.value.length &&
    inputs.userInput.selectionEnd === inputs.userInput.value.length;

  if (event.key === 'ArrowUp' && atStart) {
    event.preventDefault();
    showHistoryPrompt(-1);
  }
  if (event.key === 'ArrowDown' && atEnd) {
    event.preventDefault();
    showHistoryPrompt(1);
  }
});
inputs.userInput.addEventListener('input', () => {
  historyIndex = -1;
});

togglePanels();
updateStatusFromFlags();
loadPromptHistory();
refreshMemory().catch(() => {});
refreshKbStatus().catch(() => {});
