/**
 * Runtime Tailwind CSS artifact loader.
 *
 * The Django middleware stores the per-page input in a shared cache and writes
 * a JSON config into the page. This module fetches the compiled artifact,
 * posts the input to an HTTP compiler, or streams it over a WebSocket. It
 * never receives an API secret: token-protected APIs are Python-only.
 */

const CONFIG_PREFIX = 'daisyui-jit-config';
const STYLE_ID = 'daisyui-jit-styles';
const CONTROL_ALLOWED = '\t\n\r\f';
const BRACKETS = { '(': ')', '[': ']', '{': '}' };
const CLOSERS = new Set([')', ']', '}']);

export function validateCss(css, { complete = true } = {}) {
  if (typeof css !== 'string') {
    throw new Error('Stylesheet must be a string.');
  }
  if (!css) {
    if (complete) throw new Error('Stylesheet is empty.');
    return '';
  }
  const lowered = css.toLowerCase();
  if (
    css.includes('\0') ||
    lowered.includes('<script') ||
    lowered.includes('</style')
  ) {
    throw new Error('Stylesheet contains unsafe markup.');
  }
  for (const char of css) {
    if (char.charCodeAt(0) < 32 && !CONTROL_ALLOWED.includes(char)) {
      throw new Error('Stylesheet contains a control character.');
    }
  }
  if (complete) scanCss(css, { complete: true });
  return css;
}

function scanCss(css, { complete = true } = {}) {
  const stack = [];
  let quote = null;
  let comment = false;
  let escaped = false;

  for (let index = 0; index < css.length; index += 1) {
    const char = css[index];

    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === '\\') {
      escaped = true;
      continue;
    }
    if (comment) {
      if (char === '*' && css[index + 1] === '/') {
        comment = false;
        index += 1;
      }
      continue;
    }
    if (quote) {
      if (char === quote) quote = null;
      continue;
    }
    if (char === '/' && css[index + 1] === '*') {
      comment = true;
      index += 1;
      continue;
    }
    if (char === '"' || char === "'" || char === '`') {
      quote = char;
      continue;
    }
    if (BRACKETS[char]) {
      stack.push(BRACKETS[char]);
      continue;
    }
    if (CLOSERS.has(char)) {
      if (!stack.length || stack.pop() !== char) {
        throw new Error('Stylesheet has unbalanced brackets.');
      }
    }
  }

  if (complete && (stack.length || quote || comment || escaped)) {
    throw new Error('Stylesheet is not structurally complete.');
  }
}

function splitCompleteStatements(css) {
  const stack = [];
  let quote = null;
  let comment = false;
  let escaped = false;
  let start = 0;
  const complete = [];

  for (let index = 0; index < css.length; index += 1) {
    const char = css[index];

    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === '\\') {
      escaped = true;
      continue;
    }
    if (comment) {
      if (char === '*' && css[index + 1] === '/') {
        comment = false;
        index += 1;
      }
      continue;
    }
    if (quote) {
      if (char === quote) quote = null;
      continue;
    }
    if (char === '/' && css[index + 1] === '*') {
      comment = true;
      index += 1;
      continue;
    }
    if (char === '"' || char === "'" || char === '`') {
      quote = char;
      continue;
    }
    if (BRACKETS[char]) {
      stack.push(BRACKETS[char]);
      continue;
    }
    if (CLOSERS.has(char)) {
      if (!stack.length || stack.pop() !== char) {
        throw new Error('Stylesheet has unbalanced brackets.');
      }
      if (!stack.length && char === '}') {
        complete.push(css.slice(start, index + 1));
        start = index + 1;
      }
      continue;
    }
    if (char === ';' && !stack.length) {
      complete.push(css.slice(start, index + 1));
      start = index + 1;
    }
  }

  return { complete: complete.join(''), rest: css.slice(start) };
}

export class CssStreamBuffer {
  constructor() {
    this.buffer = '';
  }

  append(chunk) {
    validateCss(chunk, { complete: false });
    this.buffer += chunk;
    const split = splitCompleteStatements(this.buffer);
    this.buffer = split.rest;
    return split.complete;
  }

  flush() {
    const remaining = this.buffer;
    this.buffer = '';
    if (!remaining.trim()) return '';
    validateCss(remaining, { complete: true });
    return remaining;
  }
}

export function parseConfig(element) {
  if (!element || !element.textContent) return null;
  let value;
  try {
    value = JSON.parse(element.textContent);
  } catch {
    return null;
  }
  return value && typeof value === 'object' ? value : null;
}

export function apiHeaders() {
  return {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };
}

export function compileMessage(stylesheet) {
  return JSON.stringify({
    type: 'compile',
    stylesheet,
  });
}

function emit(name, detail) {
  document.dispatchEvent(
    new CustomEvent(name, { detail, bubbles: true, composed: true }),
  );
}

function injectCss(css) {
  let style = document.getElementById(STYLE_ID);
  if (!style) {
    style = document.createElement('style');
    style.id = STYLE_ID;
    document.head.appendChild(style);
  }
  style.textContent += css;
}

async function fetchText(url, { noStore = false } = {}) {
  const response = await fetch(url, {
    cache: noStore ? 'no-store' : 'default',
  });
  if (!response.ok) {
    const error = new Error(`Stylesheet request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return response.text();
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function pollOptions(config) {
  const poll = config.poll || {};
  return {
    initial: Number(poll.initial) > 0 ? Number(poll.initial) : 250,
    max: Number(poll.max) > 0 ? Number(poll.max) : 2000,
    timeout: Number(poll.timeout) > 0 ? Number(poll.timeout) : 60000,
  };
}

async function runFetch(config) {
  const css = await fetchText(config.cssUrl);
  validateCss(css);
  injectCss(css);
  return css;
}

async function runPoll(config) {
  const poll = pollOptions(config);
  const deadline = Date.now() + poll.timeout;
  let interval = poll.initial;

  while (Date.now() < deadline) {
    try {
      const css = await fetchText(config.cssUrl, { noStore: true });
      validateCss(css);
      injectCss(css);
      return css;
    } catch (error) {
      if (error.status !== 404) throw error;
    }
    await sleep(interval);
    interval = Math.min(interval * 2, poll.max);
  }
  throw new Error('Timed out waiting for Tailwind compilation.');
}

async function runHttp(config) {
  if (!config.inputUrl || !config.api?.url) {
    throw new Error('Incomplete Tailwind HTTP configuration.');
  }
  const input = await fetchText(config.inputUrl);
  validateCss(input);

  const response = await fetch(config.api.url, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify({ stylesheet: input }),
  });
  if (!response.ok) {
    throw new Error(`Tailwind HTTP compiler failed (${response.status}).`);
  }
  const payload = await response.json();
  const css = payload?.stylesheet;
  validateCss(css);
  injectCss(css);
  return css;
}

function resolveWebSocketMessage(
  event,
  ws,
  buffer,
  chunks,
  append,
  finish,
  resolve,
) {
  let message;
  try {
    message = JSON.parse(event.data);
  } catch {
    finish(new Error('Tailwind WebSocket sent invalid JSON.'));
    ws.close();
    return;
  }

  if (message.type === 'chunk') {
    try {
      append(buffer.append(String(message.css || '')));
    } catch (error) {
      finish(error);
      ws.close();
    }
    return;
  }
  if (message.type === 'error') {
    finish(
      new Error(message.message || 'Tailwind WebSocket compilation failed.'),
    );
    ws.close();
    return;
  }
  if (message.type === 'done') {
    try {
      append(buffer.flush());
      finish();
      resolve(chunks.join(''));
    } catch (error) {
      finish(error);
    }
    console.log('Compiled.');
    ws.close();
  }
}

async function runWebSocketWithRetry(
  input,
  url,
  poll,
  buffer = new CssStreamBuffer(),
  chunks = [],
  finished = false,
  retries = 5,
  delay = 1000,
) {
  return new Promise((resolve, reject) => {
    try {
      const testWs = new WebSocket(url);
    } catch (e) {
      console.log('TEST ' + e);
      return;
    }

    const ws = new WebSocket(url);

    const timer = setTimeout(() => {
      ws.close();
      reject(
        new Error('Timed out waiting for Tailwind WebSocket compilation.'),
      );
    }, poll.timeout);
    let retryTimer;

    const finish = (error) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      if (retryTimer) clearTimeout(retryTimer);
      if (error) {
        console.log('Finished with error ' + error + 'and retries ' + retries);
        reject(error);
        return;
      }
      resolve();
    };

    const append = (css) => {
      if (!css) return;
      chunks.push(css);
      injectCss(css);
    };

    ws.addEventListener('open', () => {
      ws.send(compileMessage(input));
    });

    ws.addEventListener('message', (event) =>
      resolveWebSocketMessage(
        event,
        ws,
        buffer,
        chunks,
        append,
        finish,
        resolve,
      ),
    );

    ws.addEventListener('error', (err) => {
      if (retries <= 0) {
        finish(new Error(`Tailwind WebSocket connection failed: ${err}`));
        return;
      }

      retryTimer = setTimeout(() => {
        const nextRetries = retries - 1;
        const nextDelay = delay * 2;
        runWebSocketWithRetry(
          input,
          url,
          poll,
          buffer,
          chunks,
          finished,
          nextRetries,
          nextDelay,
        )
          .then(resolve)
          .catch(finish);
      }, delay);
    });

    ws.addEventListener('close', () => finish());
  });
}

async function runWebSocket(config) {
  if (!config.inputUrl || !config.api?.url) {
    throw new Error('Incomplete Tailwind WebSocket configuration.');
  }
  const input = await fetchText(config.inputUrl);
  validateCss(input);
  const poll = pollOptions(config);

  return await runWebSocketWithRetry(input, config.api.url, poll).catch();
}

async function processConfig(element) {
  const config = parseConfig(element);
  if (!config || !config.mode) return;

  const mode = config.mode;
  emit('daisie:tailwind-pending', { mode });

  try {
    if (mode === 'error') {
      throw new Error('Tailwind compilation is unavailable.');
    }

    let css;
    if (mode === 'fetch') css = await runFetch(config);
    else if (mode === 'poll') css = await runPoll(config);
    else if (mode === 'http') css = await runHttp(config);
    else if (mode === 'ws') css = await runWebSocket(config);
    else throw new Error(`Unknown Tailwind mode: ${mode}`);

    emit('daisie:tailwind-ready', {
      mode,
      url: config.cssUrl || config.api?.url || '',
      css,
    });
  } catch (error) {
    emit('daisie:tailwind-error', {
      mode,
      error:
        error instanceof Error ? error.message : 'Tailwind compilation failed.',
    });
  }
}

function configElements(root) {
  const selector = `script[type="application/json"][id^="${CONFIG_PREFIX}"]`;
  const elements = [];
  if (root instanceof Element && root.matches(selector)) elements.push(root);
  if (root.querySelectorAll) {
    elements.push(...root.querySelectorAll(selector));
  }
  return elements;
}

function createConfigStore(document) {
  const processed = new Set();

  const scan = (root = document) => {
    for (const element of configElements(root)) {
      const key = element.id || element;
      if (processed.has(key)) continue;
      processed.add(key);
      processConfig(element);
    }
  };

  return { scan };
}

if (
  typeof document !== 'undefined' &&
  typeof MutationObserver !== 'undefined'
) {
  const store = createConfigStore(document);
  store.scan(document);

  const observer = new MutationObserver((records) => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) store.scan(node);
      }
    }
  });
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
}

export { createConfigStore };
