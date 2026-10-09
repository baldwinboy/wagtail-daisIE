/**
 * Progressive enhancement for the autocomplete multi-select control.
 *
 * The native <select multiple> is always rendered; this script hides it and
 * shows a searchable token UI. It is intentionally vanilla (no Stimulus) so it
 * works on standalone form pages as well as in the admin, and idempotent so it
 * can run once per page even when the widget and a block both load it.
 */
(function () {
  'use strict';

  if (window.__daisieAutocompleteLoaded) {
    return;
  }
  window.__daisieAutocompleteLoaded = true;

  var initialized = new WeakSet();

  function normalize(value) {
    return (value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  function selectedOptions(select) {
    return Array.prototype.filter.call(select.options, function (option) {
      return option.selected;
    });
  }

  function renderTokens(wrapper) {
    var select = wrapper.querySelector('select');
    var tokens = wrapper.querySelector('[data-daisyui-autocomplete-tokens]');
    if (!select || !tokens) {
      return;
    }
    tokens.replaceChildren();
    selectedOptions(select).forEach(function (option) {
      var token = document.createElement('span');
      token.className = 'badge badge-primary gap-1';
      token.appendChild(document.createTextNode(option.textContent));
      var remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'cursor-pointer font-bold';
      remove.setAttribute('aria-label', 'Remove ' + option.textContent);
      remove.textContent = '\u00d7';
      remove.addEventListener('click', function () {
        option.selected = false;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        renderTokens(wrapper);
      });
      token.appendChild(remove);
      tokens.appendChild(token);
    });
  }

  function filterOptions(wrapper, query) {
    var list = wrapper.querySelector('[data-daisyui-autocomplete-options]');
    if (!list) {
      return;
    }
    var search = normalize(query);
    var any = false;
    Array.prototype.forEach.call(list.children, function (item) {
      var label = normalize(item.dataset.label);
      var match = !search || label.indexOf(search) !== -1;
      item.classList.toggle('hidden', !match);
      any = any || match;
    });
    list.classList.toggle('hidden', !search || !any);
  }

  function choose(wrapper, item) {
    var select = wrapper.querySelector('select');
    var input = wrapper.querySelector('[data-daisyui-autocomplete-input]');
    if (!select || !item) {
      return;
    }
    var option = select.querySelector(
      'option[value="' + CSS.escape(item.dataset.value) + '"]',
    );
    if (option) {
      option.selected = true;
    }
    select.dispatchEvent(new Event('change', { bubbles: true }));
    renderTokens(wrapper);
    if (input) {
      input.value = '';
      input.focus();
    }
    filterOptions(wrapper, '');
  }

  function init(wrapper) {
    if (initialized.has(wrapper)) {
      return;
    }
    initialized.add(wrapper);

    var select = wrapper.querySelector('select');
    var enhanced = wrapper.querySelector(
      '[data-daisyui-autocomplete-enhanced]',
    );
    var input = wrapper.querySelector('[data-daisyui-autocomplete-input]');
    var list = wrapper.querySelector('[data-daisyui-autocomplete-options]');
    if (!select || !enhanced || !input || !list) {
      return;
    }

    select.classList.add('hidden');
    enhanced.classList.remove('hidden');

    input.addEventListener('input', function () {
      filterOptions(wrapper, input.value);
    });
    input.addEventListener('focus', function () {
      filterOptions(wrapper, input.value);
    });
    input.addEventListener('keydown', function (event) {
      if (event.key !== 'Enter') {
        return;
      }
      var first = list.querySelector('li:not(.hidden)');
      if (first) {
        event.preventDefault();
        choose(wrapper, first);
      }
    });
    list.addEventListener('click', function (event) {
      var button = event.target.closest('[data-daisyui-autocomplete-option]');
      if (button) {
        choose(wrapper, button.closest('li'));
      }
    });
    document.addEventListener('click', function (event) {
      if (!wrapper.contains(event.target)) {
        list.classList.add('hidden');
      }
    });

    renderTokens(wrapper);
  }

  function scan(root) {
    if (!root || !root.querySelectorAll) {
      return;
    }
    if (root.matches && root.matches('[data-daisyui-autocomplete]')) {
      init(root);
    }
    root.querySelectorAll('[data-daisyui-autocomplete]').forEach(init);
  }

  function ready() {
    scan(document);
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            scan(node);
          }
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ready);
  } else {
    ready();
  }
})();
