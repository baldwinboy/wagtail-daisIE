/**
 * Live-update the Feed model properties help panel.
 *
 * The panel is rendered server-side for the saved model; this script rebuilds
 * it from `window.WAGTAIL_DAISIE_CONTEXT_MODELS` when the model select changes,
 * so editors see the available properties before saving.
 */
(function () {
  'use strict';

  function esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderBody(key, meta) {
    var out = [];
    var examples = meta.examples || [];
    if (examples.length) {
      out.push('<p>Common expressions:</p><ul>');
      examples.forEach(function (example) {
        out.push('<li><code>' + esc(example) + '</code></li>');
      });
      out.push('</ul>');
    }
    var fields = meta.fields || [];
    if (fields.length) {
      out.push(
        '<table class="listing"><thead><tr><th>Property</th><th>Label</th></tr></thead><tbody>',
      );
      fields.forEach(function (field) {
        out.push(
          '<tr><td><code>' +
            esc(key ? key + '.' + field.name : field.name) +
            '</code></td><td>' +
            esc(field.label) +
            '</td></tr>',
        );
      });
      out.push('</tbody></table>');
    } else {
      out.push('<p>This model exposes no fields.</p>');
    }
    return out.join('');
  }

  function init() {
    var help = document.querySelector('[data-daisie-feed-help]');
    var select = document.querySelector('select[name$="context_model"]');
    if (!help || !select) {
      return;
    }
    select.addEventListener('change', function () {
      var key = select.value;
      var state = window.WAGTAIL_DAISIE_CONTEXT_MODELS || {};
      var meta = Object.assign({ key: key }, state[key] || {});
      var body = help.querySelector('[data-daisie-feed-help-body]');
      var summary = help.querySelector('[data-daisie-feed-help-body] summary');
      var intro = help.querySelector('[data-daisie-feed-help-intro]');
      if (!meta.label) {
        if (intro) {
          intro.textContent =
            'Choose a model to see the properties items can reference.';
        }
        if (body) {
          body.hidden = true;
        }
        return;
      }
      if (intro) {
        intro.textContent =
          'Items reference an instance of ' +
          meta.label +
          ' through the ' +
          key +
          ' variable.';
      }
      if (body) {
        body.hidden = false;
        body.innerHTML =
          '<summary style="display: list-item;">Available properties</summary>' +
          renderBody(key, meta);
      }
      if (summary) {
        summary.textContent = 'Available properties';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
