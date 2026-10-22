/**
 * Telepath widget definitions for the DaisyUI slider settings controls.
 *
 * The shared render protocol lives in widget_definition.js; the swatch widget
 * has its own definition (swatch_definition.js). The alignment widget needs no
 * client-side value handling and uses Wagtail's built-in RadioSelect adapter.
 */
(function () {
  'use strict';

  var WidgetDefinition = window.WAGTAIL_DAISIE.WidgetDefinition;

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

  function SliderSelectDefinition(html) {
    WidgetDefinition.call(this, html);
  }
  SliderSelectDefinition.prototype = Object.create(WidgetDefinition.prototype);
  SliderSelectDefinition.prototype.constructor = SliderSelectDefinition;
  SliderSelectDefinition.prototype.createBound = function (container, name) {
    return new SliderWidget(container, name);
  };

  function NumberSliderDefinition(html) {
    WidgetDefinition.call(this, html);
  }
  NumberSliderDefinition.prototype = Object.create(WidgetDefinition.prototype);
  NumberSliderDefinition.prototype.constructor = NumberSliderDefinition;
  NumberSliderDefinition.prototype.createBound = function (container, name) {
    return new NumberSliderWidget(container, name);
  };

  window.telepath.register(
    'wagtail_daisIE.widgets.SliderSelect',
    SliderSelectDefinition,
  );
  window.telepath.register(
    'wagtail_daisIE.widgets.NumberSlider',
    NumberSliderDefinition,
  );
})();
