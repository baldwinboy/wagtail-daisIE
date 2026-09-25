/* Form pages: populate model-field selects from the bound model, keep the
 * "fields available to link" help panel in sync, and offer the page's own form
 * fields as choices for the "form field" body block. */
(function () {
  function stateFor(key) {
    var state = window.WAGTAIL_DAISIE_CONTEXT_MODELS || {};
    return state[key] || null;
  }

  function instanceModelSelect() {
    return document.getElementById('id_instance_model');
  }

  function populate(select, fields) {
    var current = select.value;
    select.innerHTML = '';
    fields.forEach(function (field) {
      var option = document.createElement('option');
      option.value = field.name;
      option.textContent = field.label || field.name;
      if (field.name === current) {
        option.selected = true;
      }
      select.appendChild(option);
    });
    if (
      current &&
      !fields.some(function (field) {
        return field.name === current;
      })
    ) {
      select.value = current;
    }
  }

  function renderHelp(panel, key) {
    var meta = stateFor(key);
    var body = panel.querySelector('[data-daisie-model-fields-body]');
    var empty = panel.querySelector('[data-daisie-model-fields-empty]');
    if (!body) {
      return;
    }
    var fields = (meta && meta.fields) || [];
    body.innerHTML = fields
      .map(function (field) {
        return (
          '<tr><td><code>' +
          field.name +
          '</code></td><td>' +
          (field.label || '') +
          '</td></tr>'
        );
      })
      .join('');
    if (empty) {
      empty.hidden = fields.length > 0;
    }
  }

  function update() {
    var keySelect = instanceModelSelect();
    var key = keySelect ? keySelect.value : '';
    var meta = stateFor(key);
    var fields = (meta && meta.fields) || [];
    document
      .querySelectorAll('[data-daisie-model-field]')
      .forEach(function (select) {
        populate(select, fields);
      });
    document
      .querySelectorAll('[data-daisie-model-fields]')
      .forEach(function (panel) {
        renderHelp(panel, key);
      });
  }

  function init() {
    var keySelect = instanceModelSelect();
    if (keySelect) {
      keySelect.addEventListener('change', update);
    }
    update();
    initFormFieldSelects();
  }

  /* "Form field" body blocks: the select is rendered server-side without
   * choices, so fill it from the page's form fields. Wagtail re-renders
   * StreamField blocks as the author works, hence the MutationObserver. */
  function formFields() {
    return window.WAGTAIL_DAISIE_FORM_FIELDS || [];
  }

  function populateFormFieldSelect(select) {
    if (select.dataset.daisieFormFieldReady) {
      return;
    }
    select.dataset.daisieFormFieldReady = '1';
    var fields = formFields();
    if (!fields.length) {
      return;
    }
    var current = select.value;
    var known = false;
    select.innerHTML = '';
    fields.forEach(function (field) {
      var option = document.createElement('option');
      option.value = field.name;
      option.textContent = field.label
        ? field.label + ' (' + field.name + ')'
        : field.name;
      if (field.name === current) {
        option.selected = true;
        known = true;
      }
      select.appendChild(option);
    });
    if (current && !known) {
      // The stored field no longer exists; keep the value so the author can
      // see and fix it rather than losing it silently.
      var stale = document.createElement('option');
      stale.value = current;
      stale.textContent = current + ' (missing)';
      stale.selected = true;
      select.appendChild(stale);
    }
  }

  function initFormFieldSelects() {
    document
      .querySelectorAll('[data-daisie-form-field]')
      .forEach(populateFormFieldSelect);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  if (window.MutationObserver) {
    var pending = false;
    new MutationObserver(function () {
      if (pending) {
        return;
      }
      pending = true;
      window.requestAnimationFrame(function () {
        pending = false;
        initFormFieldSelects();
      });
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
