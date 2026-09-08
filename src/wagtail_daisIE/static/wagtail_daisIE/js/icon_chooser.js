/**
 * Provider-aware icon picker for the DaisyUI icon chooser widget.
 *
 * Searches the admin icon-search endpoint (Iconify collections, Wagtail icons,
 * webfonts, custom manifests) and writes the selected value into the widget's
 * text input. Mirrors the telepath render protocol used by block_settings.js.
 */
(function () {
  'use strict';

  function initPicker(container) {
    if (!container || container.dataset.iconReady) {
      return;
    }
    container.dataset.iconReady = '1';

    var input = container.querySelector('.daisyui-icon-widget__input');
    var search = container.querySelector('[data-icon-search]');
    var source = container.querySelector('[data-icon-source]');
    var results = container.querySelector('[data-icon-results]');
    var preview = container.querySelector('[data-icon-preview]');
    var clear = container.querySelector('[data-icon-clear]');
    var url = container.dataset.iconSearchUrl;
    var timer = null;
    var controller = null;

    function select(value, previewHtml) {
      if (input) {
        input.value = value;
      }
      if (preview) {
        preview.innerHTML = previewHtml || '';
      }
      Array.prototype.forEach.call(results.children, function (el) {
        el.classList.toggle('is-selected', el.dataset.value === value);
      });
      if (input) {
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    function render(icons) {
      results.innerHTML = '';
      icons.forEach(function (icon) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'daisyui-icon-tile';
        button.dataset.value = icon.value;
        button.title = icon.label || icon.name || icon.value;
        button.innerHTML =
          '<span class="daisyui-icon-tile__glyph">' +
          (icon.preview || '') +
          '</span>';
        button.addEventListener('click', function () {
          select(icon.value, icon.preview);
        });
        if (input && icon.value === input.value) {
          button.classList.add('is-selected');
        }
        results.appendChild(button);
      });
    }

    function load() {
      if (!url || !results) {
        return;
      }
      var params = new URLSearchParams();
      params.set('q', search ? search.value : '');
      if (source && source.value) {
        params.set('prefix', source.value);
      }
      if (controller) {
        controller.abort();
      }
      controller = 'AbortController' in window ? new AbortController() : null;
      fetch(url + '?' + params.toString(), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: controller ? controller.signal : undefined,
      })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          render(data.icons || []);
        })
        .catch(function () {
          /* aborted or failed; leave the previous results in place */
        });
    }

    function debouncedLoad() {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(load, 200);
    }

    if (search) {
      search.addEventListener('input', debouncedLoad);
      search.addEventListener('focus', function () {
        if (!results.children.length) {
          load();
        }
      });
    }
    if (source) {
      source.addEventListener('change', load);
    }
    if (clear) {
      clear.addEventListener('click', function () {
        select('', '');
      });
    }
    if (input) {
      input.addEventListener('change', function () {
        Array.prototype.forEach.call(results.children, function (el) {
          el.classList.toggle('is-selected', el.dataset.value === input.value);
        });
      });
    }

    load();
  }

  function initAll() {
    var nodes = document.querySelectorAll('[data-icon-picker]');
    for (var i = 0; i < nodes.length; i++) {
      initPicker(nodes[i]);
    }
  }

  function BoundWidget(container) {
    this.container = container;
  }

  BoundWidget.prototype.field = function () {
    return this.container.querySelector('.daisyui-icon-widget__input');
  };
  BoundWidget.prototype.getValue = function () {
    var field = this.field();
    return field ? field.value : '';
  };
  BoundWidget.prototype.getState = function () {
    return this.getValue();
  };
  BoundWidget.prototype.setState = function (state) {
    var field = this.field();
    if (field) {
      field.value = state === undefined || state === null ? '' : state;
    }
  };
  BoundWidget.prototype.setInvalid = function (invalid) {
    var field = this.field();
    if (field) {
      if (invalid) {
        field.setAttribute('aria-invalid', 'true');
      } else {
        field.removeAttribute('aria-invalid');
      }
    }
  };
  BoundWidget.prototype.focus = function () {
    var field = this.field();
    if (field && field.focus) {
      field.focus();
    }
  };

  function IconChooserDefinition(html) {
    this.html = html;
  }

  IconChooserDefinition.prototype.render = function (placeholder, name, id) {
    var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    var wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    var container = wrapper.firstElementChild;
    placeholder.replaceWith.apply(placeholder, wrapper.childNodes);
    initPicker(container);
    return new BoundWidget(container);
  };

  window.addEventListener('load', initAll);
  document.addEventListener('DOMContentLoaded', initAll);
  document.addEventListener('w-formset:ready', initAll);

  if (window.telepath) {
    window.telepath.register(
      'wagtail_daisIE.widgets.IconChooser',
      IconChooserDefinition,
    );
  }
})();
