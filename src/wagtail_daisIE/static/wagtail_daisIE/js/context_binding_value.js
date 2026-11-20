(function (root) {
  'use strict';

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderDisplay(display, state) {
    if (!display) {
      return;
    }
    if (state && state.title) {
      var link = '<a href="' + escapeHtml(state.edit_url || '') +
        '" target="_blank" rel="noopener">' + escapeHtml(state.title) + '</a>';
      display.innerHTML = link;
      return;
    }
    if (state && state.id) {
      display.innerHTML =
        '<span class="w-text-muted">' + escapeHtml('Missing instance') + '</span>';
      return;
    }
    display.innerHTML = '';
  }

  function WidgetDefinition(html) {
    this.html = html;
  }

  WidgetDefinition.prototype = Object.create(
    window.WAGTAIL_DAISIE.WidgetDefinition.prototype
  );

  WidgetDefinition.prototype.render = function (
    placeholder,
    name,
    id,
    state,
    parentCapabilities,
    options
  ) {
    var bound = window.WAGTAIL_DAISIE.WidgetDefinition.prototype.render.call(
      this,
      placeholder,
      name,
      id,
      state,
      parentCapabilities,
      options
    );
    if (state) {
      bound.setState(state);
    }
    return bound;
  };

  WidgetDefinition.prototype.createBound = function (container, name) {
    var hidden = container.querySelector('input[type="hidden"]');
    var display = container.querySelector('[data-daisie-binding-display]');
    return {
      container: container,
      hidden: hidden,
      display: display,
      getValue: function () {
        return hidden ? hidden.value : '';
      },
      getState: function () {
        return {
          id: hidden ? hidden.value : '',
          title: display ? display.textContent.trim() : '',
          edit_url: '',
        };
      },
      setState: function (state) {
        if (hidden && state) {
          hidden.value = state.id || '';
        }
        renderDisplay(display, state);
      },
    };
  };

  window.telepath.register(
    'wagtail_daisIE.widgets.ContextBindingValue',
    WidgetDefinition
  );

  // Minimal Stimulus controller used by the binding form.
  if (root.StimulusModule && root.StimulusModule.Controller) {
    var Controller = root.StimulusModule.Controller;

    class ContextBindingController extends Controller {
      connect() {
        this.root = this.element;
      }

      select(event) {
        var target = event.currentTarget;
        if (!target) {
          return;
        }
        var id = target.getAttribute('data-daisie-binding-id') || '';
        var title = target.getAttribute('data-daisie-binding-title') || '';
        var editUrl = target.getAttribute('data-daisie-binding-edit-url') || '';
        var hidden = this.root.querySelector('[data-context-binding-value]');
        var display = this.root.querySelector('[data-daisie-binding-display]');
        if (hidden) {
          hidden.value = id;
          hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        renderDisplay(display, { id: id, title: title, edit_url: editUrl });
      }

      keyChanged(event) {
        var select = event.target;
        if (!select || !select.closest('[data-contentpath="key"]')) {
          return;
        }
        var hidden = this.root.querySelector('[data-context-binding-value]');
        var display = this.root.querySelector('[data-daisie-binding-display]');
        if (hidden) {
          hidden.value = '';
        }
        if (display) {
          display.innerHTML = '';
        }
      }
    }

    root.wagtail.app.register('daisie-context-binding', ContextBindingController);
  }
})(typeof window !== 'undefined' ? window : globalThis);
