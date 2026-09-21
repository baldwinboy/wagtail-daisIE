/**
 * Context binding block: shows only the fields relevant to the selected value,
 * renders an inline model-aware help panel, and provides an accessible
 * instance chooser (search + "Show all").
 *
 * Loaded globally; metadata comes from `window.WAGTAIL_DAISIE_CONTEXT_MODELS`.
 */
(function () {
  function field(root, name) {
    return root.querySelector('[data-contentpath="' + name + '"]');
  }

  function labeledField(root, name) {
    var wrapper = field(root, name);
    return wrapper
      ? wrapper.querySelector('select, input:not([type="hidden"]), textarea')
      : null;
  }

  function toggle(el, on) {
    if (el) {
      el.style.display = on ? '' : 'none';
    }
  }

  function helpHtml(meta, mode) {
    if (!meta || !meta.label) {
      return '';
    }
    var summary =
      mode === 'fixed'
        ? 'a specific instance'
        : mode === 'url'
          ? 'from the URL'
          : esc(meta.sourceSummary || 'automatic');
    var html =
      '<p><strong>' + esc(meta.label) + '</strong> — ' + summary + '</p>';
    if (meta.examples && meta.examples.length) {
      html +=
        '<p>Use: <ul>' +
        meta.examples
          .map(function (token) {
            return '<li><code>' + esc(token) + '</code></li>';
          })
          .join('') +
        '</ul></p>';
    }
    if (meta.fields && meta.fields.length) {
      html +=
        '<details><summary style="display: list-item;">Available fields</summary><p><ul>' +
        meta.fields
          .map(function (item) {
            return (
              '<li><code>' +
              esc(item.name) +
              '</code> —' +
              esc(item.label) +
              '</li>'
            );
          })
          .join('') +
        '</ul></p></details>';
    }
    return html;
  }

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function createChooser(root) {
    var input = root.querySelector('[data-daisie-chooser-input]');
    var list = root.querySelector('[data-daisie-chooser-list]');
    var hidden = root.querySelector('[data-daisie-chooser-value]');
    var status = root.querySelector('[data-daisie-chooser-status]');
    var allButton = root.querySelector('[data-daisie-chooser-all]');
    var endpoint = root.getAttribute('data-endpoint');
    var model = '';
    var options = [];
    var active = -1;

    function setStatus(message) {
      if (status) {
        status.textContent = message || '';
      }
    }

    function setExpanded(on) {
      if (input) {
        input.setAttribute('aria-expanded', on ? 'true' : 'false');
      }
    }

    function close() {
      if (list) {
        list.hidden = true;
      }
      setExpanded(false);
      active = -1;
    }

    function choose(item) {
      if (hidden) {
        hidden.value = item.id;
      }
      if (input) {
        input.value = item.text;
      }
      close();
      setStatus('');
    }

    function render() {
      if (!list) {
        return;
      }
      list.innerHTML = '';
      if (!options.length) {
        setStatus(model ? 'No matches' : 'Choose a value first');
        close();
        return;
      }
      var current = hidden && hidden.value ? String(hidden.value) : null;
      options.forEach(function (item) {
        var option = document.createElement('li');
        option.setAttribute('role', 'option');
        option.setAttribute('data-id', item.id);
        option.setAttribute(
          'aria-selected',
          current !== null && String(item.id) === current ? 'true' : 'false',
        );
        option.className = 'daisie-chooser__option';
        option.textContent = item.text;
        option.addEventListener('mousedown', function (event) {
          event.preventDefault();
          choose(item);
        });
        list.appendChild(option);
      });
      list.hidden = false;
      setExpanded(true);
      setStatus(options.length + ' result' + (options.length === 1 ? '' : 's'));
    }

    function fetchOptions(query, limit) {
      if (!model || !endpoint) {
        options = [];
        setStatus('Choose a value first');
        return;
      }
      var params = new URLSearchParams({ model: model, limit: String(limit) });
      if (query) {
        params.set('q', query);
      }
      fetch(endpoint + '?' + params.toString(), {
        headers: { Accept: 'application/json' },
      })
        .then(function (response) {
          return response.ok ? response.json() : { results: [] };
        })
        .then(function (data) {
          options = data.results || [];
          render();
          if (limit >= 500 && options.length >= 500) {
            setStatus('Showing the first 500 — type to narrow');
          }
        })
        .catch(function () {
          options = [];
          setStatus('Could not load options');
        });
    }

    function setModel(path, selected) {
      model = path || '';
      if (hidden) {
        hidden.value = selected == null ? '' : String(selected);
      }
      if (input) {
        input.value = '';
      }
      options = [];
      if (list) {
        list.innerHTML = '';
      }
      close();
      setStatus('');
    }

    if (input) {
      input.addEventListener('focus', function () {
        if (list && list.hidden) {
          fetchOptions(input.value, 50);
        }
      });
      var timer;
      input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          fetchOptions(input.value, 50);
        }, 250);
      });
      input.addEventListener('keydown', function (event) {
        var items = list ? list.querySelectorAll('[role="option"]') : [];
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault();
          if (list && list.hidden) {
            fetchOptions(input.value, 50);
          } else if (items.length) {
            active =
              (active + (event.key === 'ArrowDown' ? 1 : -1) + items.length) %
              items.length;
            Array.prototype.forEach.call(items, function (item, index) {
              item.setAttribute(
                'aria-selected',
                index === active ? 'true' : 'false',
              );
              item.classList.toggle('is-active', index === active);
            });
            items[active].scrollIntoView({ block: 'nearest' });
          }
        } else if (event.key === 'Enter') {
          if (active >= 0 && items[active]) {
            event.preventDefault();
            choose(options[active]);
          }
        } else if (event.key === 'Escape') {
          close();
        }
      });
      input.addEventListener('blur', function () {
        window.setTimeout(close, 150);
      });
    }
    if (allButton) {
      allButton.addEventListener('click', function () {
        fetchOptions('', 500);
      });
    }

    return { setModel: setModel };
  }

  function findRoot(el) {
    var wrapper = el.closest('[data-contentpath="object_id"]');
    if (!wrapper) {
      return null;
    }
    var node = wrapper.parentElement;
    while (node && node !== document.body) {
      if (
        node.querySelector &&
        node.querySelector('[data-contentpath="key"]')
      ) {
        return node;
      }
      node = node.parentElement;
    }
    return null;
  }

  function initBinding(chooserEl) {
    if (chooserEl.dataset.daisieBindingReady) {
      return;
    }
    var root = findRoot(chooserEl);
    if (!root) {
      return;
    }
    chooserEl.dataset.daisieBindingReady = '1';

    var keyEl = labeledField(root, 'key');
    var modeEl = labeledField(root, 'mode');
    var keyWrap = field(root, 'key');
    var modeWrap = field(root, 'mode');
    var lookupWrap = field(root, 'lookup_field');
    var instanceWrap = field(root, 'object_id');
    var state = window.WAGTAIL_DAISIE_CONTEXT_MODELS || {};
    var chooser = createChooser(chooserEl);
    if (!keyEl) {
      return;
    }

    var help = document.createElement('div');
    help.className = 'daisie-binding-help help-block help-info';
    if (keyWrap && keyWrap.parentElement) {
      keyWrap.insertAdjacentElement('afterend', help);
    }

    var lastKey = null;
    var meta = {};

    function update() {
      meta = state[keyEl.value] || {};
      var modes = meta.modes || ['automatic'];
      var changed = lastKey !== keyEl.value;
      lastKey = keyEl.value;

      if (modeEl) {
        Array.prototype.forEach.call(modeEl.options, function (option) {
          var valid = modes.indexOf(option.value) !== -1;
          option.hidden = !valid;
          option.disabled = !valid;
        });
        if (modes.indexOf(modeEl.value) === -1) {
          modeEl.value = modes[0];
        }
      }
      var mode = modeEl ? modeEl.value : 'automatic';
      toggle(modeWrap, modes.length > 1);
      toggle(lookupWrap, mode === 'url');
      toggle(instanceWrap, mode === 'fixed');
      help.innerHTML = helpHtml(
        Object.assign({ key: keyEl.value }, meta),
        mode,
      );

      if (mode === 'fixed') {
        var hiddenInput = chooserEl.querySelector(
          '[data-daisie-chooser-value]',
        );
        chooser.setModel(
          meta.modelPath,
          changed ? null : hiddenInput ? hiddenInput.value : null,
        );
      }
    }

    keyEl.addEventListener('change', update);
    if (modeEl) {
      modeEl.addEventListener('change', update);
    }
    update();
  }

  function initAll() {
    document.querySelectorAll('[data-daisie-chooser]').forEach(initBinding);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  if (window.MutationObserver) {
    var scheduled = false;
    new MutationObserver(function () {
      if (scheduled) {
        return;
      }
      scheduled = true;
      window.requestAnimationFrame(function () {
        scheduled = false;
        initAll();
      });
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
