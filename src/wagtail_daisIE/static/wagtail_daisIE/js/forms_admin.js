/* Form pages: populate model-field selects from the bound model and keep the
 * "fields available to link" help panel in sync. */
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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
