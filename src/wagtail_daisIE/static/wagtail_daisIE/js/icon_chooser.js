/**
 * Provider-aware icon picker for the DaisyUI icon chooser widget.
 *
 * Registered as a Stimulus controller so it initialises automatically for
 * widgets added dynamically (StreamField blocks, InlinePanel, modals) without
 * any manual DOM scanning. The widget's value/state is handled by Wagtail's
 * built-in ``wagtail.widgets.Widget`` telepath widget; this controller only
 * drives the search UI and the visual preview.
 *
 * Searches the admin icon-search endpoint (Iconify collections, Wagtail icons,
 * webfonts, custom manifests) and writes the selected value into the widget's
 * text input.
 */
(function () {
  'use strict';

  class IconChooserController extends window.StimulusModule.Controller {
    connect() {
      this.input = this.element.querySelector('.daisyui-icon-widget__input');
      this.search = this.element.querySelector('[data-icon-search]');
      this.source = this.element.querySelector('[data-icon-source]');
      this.results = this.element.querySelector('[data-icon-results]');
      this.preview = this.element.querySelector('[data-icon-preview]');
      this.clear = this.element.querySelector('[data-icon-clear]');
      this.url = this.element.dataset.iconSearchUrl;
      this.timer = null;
      this.controller = null;

      if (this.search) {
        this.onSearchInput = this.debouncedLoad.bind(this);
        this.onSearchFocus = this.onFocus.bind(this);
        this.search.addEventListener('input', this.onSearchInput);
        this.search.addEventListener('focus', this.onSearchFocus);
      }
      if (this.source) {
        this.onSourceChange = this.load.bind(this);
        this.source.addEventListener('change', this.onSourceChange);
      }
      if (this.clear) {
        this.onClear = this.select.bind(this, '', '');
        this.clear.addEventListener('click', this.onClear);
      }
      if (this.input) {
        this.onInputChange = this.syncSelection.bind(this);
        this.input.addEventListener('change', this.onInputChange);
      }

      // The base widget has already applied the restored value synchronously
      // (Stimulus connects asynchronously), so render its preview now.
      if (this.input && this.input.value) {
        this.updatePreview(this.input.value);
      }
      this.load();
    }

    disconnect() {
      if (this.timer) {
        clearTimeout(this.timer);
      }
      if (this.controller) {
        this.controller.abort();
      }
      if (this.search) {
        this.search.removeEventListener('input', this.onSearchInput);
        this.search.removeEventListener('focus', this.onSearchFocus);
      }
      if (this.source) {
        this.source.removeEventListener('change', this.onSourceChange);
      }
      if (this.clear) {
        this.clear.removeEventListener('click', this.onClear);
      }
      if (this.input) {
        this.input.removeEventListener('change', this.onInputChange);
      }
    }

    select(value, previewHtml) {
      if (this.input) {
        this.input.value = value;
      }
      if (this.preview) {
        this.preview.innerHTML = previewHtml || '';
      }
      this.markSelected(value);
      if (this.input) {
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    markSelected(value) {
      if (!this.results) {
        return;
      }
      Array.prototype.forEach.call(this.results.children, function (el) {
        el.classList.toggle('is-selected', el.dataset.value === value);
      });
    }

    syncSelection() {
      if (this.input) {
        this.markSelected(this.input.value);
      }
    }

    updatePreview(value) {
      if (!this.preview) {
        return;
      }
      if (!value || !this.url) {
        this.preview.innerHTML = '';
        return;
      }
      fetch(this.url + '?value=' + encodeURIComponent(value), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
        .then(function (response) {
          return response.json();
        })
        .then((data) => {
          if (data.preview) {
            this.preview.innerHTML = data.preview;
          }
        })
        .catch(function () {
          /* leave the previous preview in place */
        });
    }

    render(icons) {
      var self = this;
      if (!this.results) {
        return;
      }
      this.results.innerHTML = '';
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
          self.select(icon.value, icon.preview);
        });
        if (self.input && icon.value === self.input.value) {
          button.classList.add('is-selected');
        }
        self.results.appendChild(button);
      });
    }

    load() {
      if (!this.url || !this.results) {
        return;
      }
      var params = new URLSearchParams();
      params.set('q', this.search ? this.search.value : '');
      if (this.source && this.source.value) {
        params.set('prefix', this.source.value);
      }
      if (this.controller) {
        this.controller.abort();
      }
      this.controller =
        'AbortController' in window ? new AbortController() : null;
      fetch(this.url + '?' + params.toString(), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: this.controller ? this.controller.signal : undefined,
      })
        .then(function (response) {
          return response.json();
        })
        .then((data) => {
          this.render(data.icons || []);
        })
        .catch(function () {
          /* aborted or failed; leave the previous results in place */
        });
    }

    debouncedLoad() {
      if (this.timer) {
        clearTimeout(this.timer);
      }
      this.timer = setTimeout(this.load.bind(this), 200);
    }

    onFocus() {
      if (this.results && !this.results.children.length) {
        this.load();
      }
    }
  }

  window.wagtail.app.register('daisie-icon', IconChooserController);
})();
