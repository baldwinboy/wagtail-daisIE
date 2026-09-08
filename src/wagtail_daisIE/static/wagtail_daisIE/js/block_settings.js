/**
 * Telepath widget definitions for the DaisyUI StreamBlock settings controls
 * (colour swatches, preset sliders and text-alignment icons).
 *
 * Mirrors the render protocol used by Wagtail's generic widget definitions in
 * wagtailadmin/js/telepath/widgets.js and registers each constructor under the
 * names declared by the corresponding Python adapters in
 * wagtail_daisIE/telepath.py.
 */
(function () {
  'use strict';

  function applyAttributes(el, attrs) {
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key)) {
        el.setAttribute(key, attrs[key]);
      }
    }
  }

  /**
   * Shared definition: splices the server-rendered widget HTML (with the
   * __NAME__/__ID__ tokens) into the DOM and returns a bound widget.
   */
  function BaseDefinition(html) {
    this.html = html;
  }

  BaseDefinition.prototype.render = function (
    placeholder,
    name,
    id,
    state,
    parentCapabilities,
    options,
  ) {
    var html = this.html.replace(/__NAME__/g, name).replace(/__ID__/g, id);
    var wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    var container = wrapper.firstElementChild;
    placeholder.replaceWith.apply(placeholder, wrapper.childNodes);
    if (options && options.attributes) {
      applyAttributes(container, options.attributes);
    }
    var bound = this.createBound(container, name);
    if (state !== undefined && state !== null) {
      bound.setState(state);
    }
    return bound;
  };

  /**
   * Bound widget for radio-tile controls (swatches and alignment icons).
   */
  function RadioTileWidget(container, name) {
    this.container = container;
    this.inputs = Array.prototype.slice.call(
      container.querySelectorAll('input[type="radio"][name="' + name + '"]'),
    );
    this.idForLabel =
      container.id || (this.inputs[0] && this.inputs[0].id) || '';
  }

  RadioTileWidget.prototype.selected = function () {
    for (var i = 0; i < this.inputs.length; i++) {
      if (this.inputs[i].checked) {
        return this.inputs[i];
      }
    }
    return null;
  };

  RadioTileWidget.prototype.getValue = function () {
    var input = this.selected();
    return input ? input.value : '';
  };

  RadioTileWidget.prototype.getState = function () {
    return this.getValue();
  };

  RadioTileWidget.prototype.customRadio = function () {
    for (var i = 0; i < this.inputs.length; i++) {
      if (this.inputs[i].classList.contains('daisyui-swatch-radio--custom')) {
        return this.inputs[i];
      }
    }
    return null;
  };

  /**
   * Extract the bare hex from a stored custom value. Class-based swatches store
   * ``"<prefix>-[#rrggbb]"`` while raw swatches store ``"#rrggbb"``.
   */
  RadioTileWidget.prototype.parseCustomValue = function (customRadio, str) {
    if (!customRadio || !str) {
      return null;
    }
    if (customRadio.getAttribute('data-raw') === 'true') {
      var raw = /^#([0-9a-fA-F]{3,8})$/.exec(str);
      return raw ? raw[1] : null;
    }
    var match = /^([a-z-]+)-\[#([0-9a-fA-F]{3,8})\]$/.exec(str);
    if (!match) {
      return null;
    }
    var prefix = customRadio.getAttribute('data-prefix') || '';
    return match[1] === prefix ? match[2] : null;
  };

  RadioTileWidget.prototype.applyCustomColor = function (hex) {
    var customInput = this.container.querySelector('.daisyui-coloris-input');
    var customChip = this.container.querySelector(
      '.daisyui-swatch-chip--custom',
    );
    var color = hex ? '#' + hex : '';
    if (customInput) {
      customInput.value = color;
    }
    if (customChip) {
      // Show the chosen colour instead of the "empty" checkerboard once set.
      customChip.style.backgroundColor = color;
      customChip.style.backgroundImage = hex ? 'none' : '';
    }
  };

  RadioTileWidget.prototype.setState = function (value) {
    var str = value === undefined || value === null ? '' : String(value);
    var customRadio = this.customRadio();
    var i;

    // A preset radio whose value matches the state wins outright. This also
    // distinguishes raw swatches, whose preset and custom values are both
    // plain hex strings.
    var preset = null;
    for (i = 0; i < this.inputs.length; i++) {
      if (this.inputs[i] !== customRadio && this.inputs[i].value === str) {
        preset = this.inputs[i];
        break;
      }
    }

    if (preset) {
      for (i = 0; i < this.inputs.length; i++) {
        this.inputs[i].checked = this.inputs[i] === preset;
      }
      if (customRadio) {
        customRadio.value = '';
      }
      this.applyCustomColor('');
      return;
    }

    // The Telepath template renders the custom tile with an empty value, so a
    // stored custom value has to be re-applied here after save/reload.
    var hex = this.parseCustomValue(customRadio, str);
    if (customRadio && hex !== null) {
      for (i = 0; i < this.inputs.length; i++) {
        this.inputs[i].checked = this.inputs[i] === customRadio;
      }
      customRadio.value = str;
      this.applyCustomColor(hex);
      return;
    }

    for (i = 0; i < this.inputs.length; i++) {
      this.inputs[i].checked = false;
    }
    if (customRadio) {
      customRadio.value = '';
    }
    this.applyCustomColor('');
  };

  RadioTileWidget.prototype.setInvalid = function (invalid) {
    for (var i = 0; i < this.inputs.length; i++) {
      if (invalid) {
        this.inputs[i].setAttribute('aria-invalid', 'true');
      } else {
        this.inputs[i].removeAttribute('aria-invalid');
      }
    }
  };

  RadioTileWidget.prototype.getTextLabel = function () {
    var input = this.selected();
    if (!input) {
      return null;
    }
    var label = input.closest('label');
    return label ? label.textContent.trim() : input.value;
  };

  RadioTileWidget.prototype.focus = function () {
    var input = this.selected() || this.inputs[0];
    if (input && input.focus) {
      input.focus();
    }
  };

  /**
   * Bound widget for the preset slider control.
   * The <select> is the real value carrier; the range input is the visual
   * control, kept in sync with the select.
   */
  function SliderWidget(container, name) {
    this.container = container;
    this.select = container.querySelector('select[name="' + name + '"]');
    this.range = container.querySelector('.daisyui-slider-range');
    this.valueLabel = container.querySelector('.daisyui-slider-value');
    this.values = Array.prototype.map.call(
      this.select.options,
      function (option) {
        return option.value;
      },
    );
    this.texts = Array.prototype.map.call(
      this.select.options,
      function (option) {
        return option.text;
      },
    );
    this.idForLabel = container.id || this.select.id || '';

    var self = this;
    if (this.range) {
      this.range.addEventListener('input', function () {
        var index = parseInt(this.value, 10) || 0;
        self.select.value = self.values[index] || '';
        self.updateLabel();
      });
    }
  }

  SliderWidget.prototype.getValue = function () {
    return this.select.value;
  };

  SliderWidget.prototype.getState = function () {
    return this.getValue();
  };

  SliderWidget.prototype.setState = function (value) {
    var index = this.values.indexOf(String(value));
    if (index === -1) {
      index = 0;
    }
    this.select.value = this.values[index] || '';
    if (this.range) {
      this.range.value = index;
    }
    this.updateLabel();
  };

  SliderWidget.prototype.setInvalid = function (invalid) {
    if (invalid) {
      this.select.setAttribute('aria-invalid', 'true');
    } else {
      this.select.removeAttribute('aria-invalid');
    }
  };

  SliderWidget.prototype.getTextLabel = function () {
    var index = parseInt(this.range ? this.range.value : 0, 10) || 0;
    return this.texts[index] || this.select.value;
  };

  SliderWidget.prototype.updateLabel = function () {
    if (this.valueLabel) {
      var index = parseInt(this.range ? this.range.value : 0, 10) || 0;
      this.valueLabel.textContent =
        this.texts[index] || this.select.value || '';
    }
  };

  SliderWidget.prototype.focus = function () {
    if (this.range && this.range.focus) {
      this.range.focus();
    } else if (this.select && this.select.focus) {
      this.select.focus();
    }
  };

  /**
   * Bound widget for the continuous numeric slider.
   * The number <input> is the real value carrier; the range input is the
   * visual control, kept in sync in both directions. An empty value maps to
   * "None" and resets the range to its minimum.
   */
  function NumberSliderWidget(container, name) {
    this.container = container;
    this.number = container.querySelector(
      'input[type="number"][name="' + name + '"]',
    );
    this.range = container.querySelector('.daisyui-slider-range');
    this.valueLabel = container.querySelector('.daisyui-slider-value');
    this.min = parseInt(
      (this.range && this.range.getAttribute('min')) || '0',
      10,
    );
    this.max = parseInt(
      (this.range && this.range.getAttribute('max')) || '100',
      10,
    );
    this.suffix =
      (this.valueLabel && this.valueLabel.getAttribute('data-suffix')) || '';
    this.idForLabel = container.id || this.number.id || '';

    var self = this;
    if (this.range) {
      this.range.addEventListener('input', function () {
        if (self.number) {
          self.number.value = this.value;
        }
        self.updateLabel();
      });
    }
    if (this.number) {
      this.number.addEventListener('input', function () {
        self.syncFromNumber();
      });
      this.number.addEventListener('change', function () {
        self.syncFromNumber();
      });
    }
  }

  NumberSliderWidget.prototype.getValue = function () {
    return this.number ? this.number.value : '';
  };

  NumberSliderWidget.prototype.getState = function () {
    return this.getValue();
  };

  NumberSliderWidget.prototype.setState = function (value) {
    if (this.number) {
      this.number.value =
        value === null || value === undefined || value === ''
          ? ''
          : String(value);
    }
    this.syncFromNumber();
  };

  NumberSliderWidget.prototype.syncFromNumber = function () {
    var raw = this.number ? this.number.value : '';
    var parsed = parseInt(raw, 10);
    if (isNaN(parsed)) {
      if (this.range) {
        this.range.value = this.min;
      }
      this.updateLabel();
      return;
    }
    parsed = Math.min(Math.max(parsed, this.min), this.max);
    if (this.number && this.number.value !== String(parsed)) {
      this.number.value = parsed;
    }
    if (this.range) {
      this.range.value = parsed;
    }
    this.updateLabel();
  };

  NumberSliderWidget.prototype.setInvalid = function (invalid) {
    if (!this.number) {
      return;
    }
    if (invalid) {
      this.number.setAttribute('aria-invalid', 'true');
    } else {
      this.number.removeAttribute('aria-invalid');
    }
  };

  NumberSliderWidget.prototype.getTextLabel = function () {
    var raw = this.number ? this.number.value : '';
    return raw === '' ? '' : raw + this.suffix;
  };

  NumberSliderWidget.prototype.updateLabel = function () {
    if (!this.valueLabel) {
      return;
    }
    var raw = this.number ? this.number.value : '';
    this.valueLabel.textContent = raw === '' ? 'None' : raw + this.suffix;
  };

  NumberSliderWidget.prototype.focus = function () {
    if (this.number && this.number.focus) {
      this.number.focus();
    } else if (this.range && this.range.focus) {
      this.range.focus();
    }
  };

  function SwatchSelectDefinition(html) {
    BaseDefinition.call(this, html);
  }
  SwatchSelectDefinition.prototype = Object.create(BaseDefinition.prototype);
  SwatchSelectDefinition.prototype.constructor = SwatchSelectDefinition;
  SwatchSelectDefinition.prototype.createBound = function (container, name) {
    var widget = new RadioTileWidget(container, name);
    initColorisForSwatch(container);
    return widget;
  };

  /**
   * The swatch widget whose "Custom" tile currently shows the inline picker.
   * Coloris keeps a single physical picker, so only one widget can be active
   * at a time; the picker is moved to its container when activated.
   */
  var activeSwatchContainer = null;

  // In inline mode Coloris leaves `currentEl` unset and never writes to the
  // bound input, so picks are read from the document-level coloris:pick event
  // and fed into the active widget's regular input handler.
  document.addEventListener('coloris:pick', function (event) {
    var container = activeSwatchContainer;
    if (!container) return;
    var input = container.querySelector('.daisyui-coloris-input');
    var color = event.detail && event.detail.color;
    if (!input || color === undefined || color === null) return;
    input.value = color;
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });

  // Clicking anywhere outside the active widget dismisses the inline picker.
  document.addEventListener('click', function (event) {
    var container = activeSwatchContainer;
    if (!container) return;
    if (container.contains(event.target)) return;
    activeSwatchContainer = null;
    try {
      Coloris({ inline: false });
    } catch (_e) {
      /* ignore */
    }
  });

  function initColorisForSwatch(container) {
    if (container.hasAttribute('data-coloris-ready')) return;

    var input = container.querySelector('.daisyui-coloris-input');
    var customRadio = container.querySelector('.daisyui-swatch-radio--custom');
    if (!input || !customRadio || typeof Coloris === 'undefined') return;

    var optionsAttr = container.getAttribute('data-daisyui-coloris-options');
    var options = {};
    if (optionsAttr) {
      try {
        options = JSON.parse(optionsAttr);
      } catch (_e) {
        /* ignore */
      }
    }

    var isRaw = customRadio.getAttribute('data-raw') === 'true';
    var prefix = isRaw ? '' : customRadio.getAttribute('data-prefix') || '';
    var anchor = container.getAttribute('data-daisyui-coloris-parent');
    var parent =
      (anchor ? '#' + anchor : '') ||
      (container.id ? '#' + container.id : '') ||
      options.parent ||
      'body';
    var bound = false;

    function currentColor() {
      // Opening the inline picker re-seeds its colour from `defaultColor`;
      // without it Coloris falls back to its own black default. Normalise the
      // stored value to a bare hex and fall back to white when it is empty or
      // not a colour.
      var match = /#?([0-9a-fA-F]{3,8})/.exec((input.value || '').trim());
      return match ? '#' + match[1] : '#ffffff';
    }

    function activateInline() {
      var config = {
        parent: parent,
        defaultColor: currentColor(),
        swatches: options.swatches || [],
        swatchesOnly: options.swatchesOnly || false,
        format: options.format || 'hex',
        alpha: options.alpha || false,
        inline: true,
      };
      if (!bound) {
        // Bind the field only the first time the custom tile is activated;
        // re-applying ``el`` on later activations would rebind listeners. The
        // widget renders its own colour chip, so skip Coloris's wrapping too.
        config.el = input;
        config.wrap = false;
        bound = true;
      }
      try {
        Coloris(config);
      } catch (_e) {
        return;
      }
      activeSwatchContainer = container;

      // The settings panel can still be settling when the picker is first
      // shown, which leaves Coloris with stale/zero colour-area geometry.
      // Re-measure once the layout has settled.
      if (window.requestAnimationFrame) {
        window.requestAnimationFrame(function () {
          try {
            Coloris.updatePosition();
          } catch (_e) {
            /* ignore */
          }
        });
      }
    }

    function deactivateInline() {
      activeSwatchContainer = null;
      try {
        Coloris({ inline: false });
      } catch (_e) {
        /* ignore */
      }
    }

    container.setAttribute('data-coloris-ready', '1');

    // The Coloris picker is only rendered inline once the "Custom" tile is
    // chosen; until then the text field stays a plain input.
    var tile = customRadio.closest('.daisyui-swatch-tile');
    if (tile) {
      tile.addEventListener('click', function (event) {
        if (event.target === input) return;
        event.preventDefault();
        customRadio.checked = true;
        if (activeSwatchContainer === container) {
          deactivateInline();
        } else {
          activateInline();
        }
      });
    }

    input.addEventListener('focus', function () {
      customRadio.checked = true;
      activateInline();
    });

    // Choosing a preset swatch dismisses the inline picker again.
    Array.prototype.forEach.call(
      container.querySelectorAll(
        '.daisyui-swatch-radio:not(.daisyui-swatch-radio--custom)',
      ),
      function (radio) {
        radio.addEventListener('change', function () {
          if (radio.checked) deactivateInline();
        });
      },
    );

    input.addEventListener('input', function () {
      var color = (input.value || '').trim();
      var match = /^#?([0-9a-fA-F]{3,8})$/.exec(color);
      if (!match) {
        customRadio.value = '';
        return;
      }
      var hex = match[1];
      customRadio.value = isRaw ? '#' + hex : prefix + '-[#' + hex + ']';
      customRadio.checked = true;

      var chip = customRadio
        .closest('label')
        .querySelector('.daisyui-swatch-chip--custom');
      if (chip) {
        chip.style.backgroundColor = '#' + hex;
        chip.style.backgroundImage = 'none';
      }

      customRadio.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }

  // Initialise any server-rendered swatches that telepath did not create.
  function initAllSwatches() {
    var containers = document.querySelectorAll('.daisyui-swatch-widget');
    for (var i = 0; i < containers.length; i++) {
      initColorisForSwatch(containers[i]);
    }
  }

  window.addEventListener('load', initAllSwatches);
  document.addEventListener('w-formset:ready', initAllSwatches);

  // Initialise any server-rendered sliders that telepath did not create.
  function initAllSliders() {
    var containers = document.querySelectorAll('.daisyui-slider-widget');
    for (var i = 0; i < containers.length; i++) {
      var container = containers[i];
      var select = container.querySelector('select');
      if (select && !container.hasAttribute('data-slider-ready')) {
        container.setAttribute('data-slider-ready', '1');
        new SliderWidget(container, select.name).setState(select.value);
      }
    }
  }

  window.addEventListener('load', initAllSliders);
  document.addEventListener('w-formset:ready', initAllSliders);

  // Initialise any server-rendered numeric sliders that telepath did not create.
  function initAllNumberSliders() {
    var containers = document.querySelectorAll('.daisyui-number-slider-widget');
    for (var i = 0; i < containers.length; i++) {
      var container = containers[i];
      var number = container.querySelector('input[type="number"]');
      if (number && !container.hasAttribute('data-number-slider-ready')) {
        container.setAttribute('data-number-slider-ready', '1');
        new NumberSliderWidget(container, number.name).setState(number.value);
      }
    }
  }

  window.addEventListener('load', initAllNumberSliders);
  document.addEventListener('w-formset:ready', initAllNumberSliders);

  function AlignSelectDefinition(html) {
    BaseDefinition.call(this, html);
  }
  AlignSelectDefinition.prototype = Object.create(BaseDefinition.prototype);
  AlignSelectDefinition.prototype.constructor = AlignSelectDefinition;
  AlignSelectDefinition.prototype.createBound = function (container, name) {
    return new RadioTileWidget(container, name);
  };

  function SliderSelectDefinition(html) {
    BaseDefinition.call(this, html);
  }
  SliderSelectDefinition.prototype = Object.create(BaseDefinition.prototype);
  SliderSelectDefinition.prototype.constructor = SliderSelectDefinition;
  SliderSelectDefinition.prototype.createBound = function (container, name) {
    return new SliderWidget(container, name);
  };

  function NumberSliderDefinition(html) {
    BaseDefinition.call(this, html);
  }
  NumberSliderDefinition.prototype = Object.create(BaseDefinition.prototype);
  NumberSliderDefinition.prototype.constructor = NumberSliderDefinition;
  NumberSliderDefinition.prototype.createBound = function (container, name) {
    return new NumberSliderWidget(container, name);
  };

  window.telepath.register(
    'wagtail_daisIE.widgets.SwatchSelect',
    SwatchSelectDefinition,
  );
  window.telepath.register(
    'wagtail_daisIE.widgets.SliderSelect',
    SliderSelectDefinition,
  );
  window.telepath.register(
    'wagtail_daisIE.widgets.NumberSlider',
    NumberSliderDefinition,
  );
  window.telepath.register(
    'wagtail_daisIE.widgets.AlignSelect',
    AlignSelectDefinition,
  );
})();
