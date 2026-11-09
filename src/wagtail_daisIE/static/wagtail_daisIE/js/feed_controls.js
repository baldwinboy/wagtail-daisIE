(function () {
  'use strict';

  if (window.__daisieFeedControlsLoaded) {
    return;
  }
  window.__daisieFeedControlsLoaded = true;

  function selectedClasses(element) {
    return (element.getAttribute('data-daisie-selected-class') || 'btn-active')
      .trim()
      .split(/\s+/)
      .filter(Boolean);
  }

  function targetFor(input) {
    return input.closest('[data-daisie-selected-class]') || input;
  }

  function sync(input) {
    var target = targetFor(input);
    selectedClasses(target).forEach(function (name) {
      target.classList.toggle(name, input.checked);
    });
  }

  function syncGroup(input) {
    var form = input.form || input.closest('form');
    if (input.type === 'radio' && input.name && form) {
      form.querySelectorAll('input[type="radio"]').forEach(function (radio) {
        if (radio.name === input.name) {
          sync(radio);
        }
      });
      return;
    }
    sync(input);
  }

  function syncAll(root) {
    (root || document)
      .querySelectorAll('[data-daisie-selectable]')
      .forEach(sync);
  }

  document.addEventListener('change', function (event) {
    var input = event.target.closest('[data-daisie-selectable]');
    if (input) {
      syncGroup(input);
    }
  });

  function updateUrl(form) {
    if (
      !window.history ||
      !window.history.replaceState ||
      !window.URLSearchParams ||
      !window.FormData
    ) {
      return;
    }

    var params = new URLSearchParams(window.location.search);
    Array.from(params.keys()).forEach(function (key) {
      if (
        key.indexOf('filter_') === 0 ||
        key === 'feed_search' ||
        key === 'layout'
      ) {
        params.delete(key);
      }
    });

    ['limit', 'offset', 'block', 'layout_token', 'page'].forEach(
      function (key) {
        params.delete(key);
      },
    );

    new FormData(form).forEach(function (value, key) {
      if (
        key === 'block' ||
        key === 'offset' ||
        key === 'limit' ||
        key === 'layout_token' ||
        key === 'page' ||
        value === ''
      ) {
        return;
      }
      params.append(key, value);
    });

    var query = params.toString();
    try {
      window.history.replaceState(
        null,
        '',
        window.location.pathname + (query ? '?' + query : ''),
      );
    } catch (_error) {
      /* URL updates are progressive enhancement only. */
    }
  }

  document.addEventListener('htmx:afterRequest', function (event) {
    if (!event.detail || event.detail.successful === false) {
      return;
    }
    var trigger = event.detail.elt;
    if (!trigger || !trigger.closest) {
      return;
    }
    if (!trigger.matches('[data-daisie-feed-form], [data-daisie-feed-more]')) {
      return;
    }
    var root = trigger.closest('[data-daisie-feed]');
    if (!root) {
      return;
    }
    var forms = root.querySelectorAll('[data-daisie-feed-form]');
    if (forms.length === 1) {
      updateUrl(forms[0]);
    }
  });

  function ready() {
    syncAll(document);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ready);
  } else {
    ready();
  }
  window.addEventListener('pageshow', ready);
})();
