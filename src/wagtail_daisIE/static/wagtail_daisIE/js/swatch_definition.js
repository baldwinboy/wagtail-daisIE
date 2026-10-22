/**
 * Telepath definition for the DaisyUI colour swatch widget.
 *
 * This bound widget owns value/state mapping only (the custom radio stores a
 * ``bg-[#rrggbb]`` or raw ``#rrggbb`` value, which the generic RadioSelect
 * bound widget cannot restore). The Coloris picker behaviour lives in
 * swatch_controller.js; this file never touches Coloris.
 *
 * Presentation is decoupled through ``data-daisie-swatch-target`` attributes
 * rather than styling classes.
 */
(function () {
  'use strict';

  var WidgetDefinition = window.WAGTAIL_DAISIE.WidgetDefinition;

  function SwatchBoundWidget(container, name) {
    this.container = container;
    this.inputs = Array.prototype.slice.call(
      container.querySelectorAll('input[type="radio"][name="' + name + '"]'),
    );
    this.radio = container.querySelector('[data-daisie-swatch-target="radio"]');
    this.input = container.querySelector('[data-daisie-swatch-target="input"]');
    // The definition container is the accordion root; the prefix value lives
    // on the inner widget element that also hosts the Stimulus controller.
    this.root =
      container.querySelector('[data-daisie-swatch-prefix-value]') || container;
    this.prefix = this.root.dataset.daisieSwatchPrefixValue || '';
    this.idForLabel =
      this.root.id || (this.inputs[0] && this.inputs[0].id) || '';
  }

  SwatchBoundWidget.prototype.selected = function () {
    for (var i = 0; i < this.inputs.length; i++) {
      if (this.inputs[i].checked) {
        return this.inputs[i];
      }
    }
    return null;
  };

  SwatchBoundWidget.prototype.getValue = function () {
    var input = this.selected();
    return input ? input.value : '';
  };

  SwatchBoundWidget.prototype.getState = function () {
    return this.getValue();
  };

  SwatchBoundWidget.prototype.parseCustomValue = function (str) {
    if (!this.radio || !str) {
      return null;
    }
    if (this.radio.dataset.raw === 'true') {
      var raw = /^#([0-9a-fA-F]{3,8})$/.exec(str);
      return raw ? raw[1] : null;
    }
    var match = /^([a-z-]+)-\[#([0-9a-fA-F]{3,8})\]$/.exec(str);
    return match && match[1] === this.prefix ? match[2] : null;
  };

  SwatchBoundWidget.prototype.setInputValue = function (hex) {
    // The Stimulus controller renders the chip from this value; keeping the
    // input as the single source avoids duplicating chip styling here.
    if (this.input) {
      this.input.value = hex ? '#' + hex : '';
    }
  };

  SwatchBoundWidget.prototype.setState = function (value) {
    var str = value === undefined || value === null ? '' : String(value);
    var i;
    var preset = null;

    // A preset radio whose value matches the state wins outright.
    for (i = 0; i < this.inputs.length; i++) {
      if (this.inputs[i] !== this.radio && this.inputs[i].value === str) {
        preset = this.inputs[i];
        break;
      }
    }

    if (preset) {
      for (i = 0; i < this.inputs.length; i++) {
        this.inputs[i].checked = this.inputs[i] === preset;
      }
      if (this.radio) {
        this.radio.value = '';
      }
      this.setInputValue(null);
      return;
    }

    // The Telepath template renders the custom tile value-less, so a stored
    // custom value has to be re-applied here after save/reload.
    var hex = this.parseCustomValue(str);
    if (this.radio && hex !== null) {
      for (i = 0; i < this.inputs.length; i++) {
        this.inputs[i].checked = this.inputs[i] === this.radio;
      }
      this.radio.value = str;
      this.setInputValue(hex);
      return;
    }

    for (i = 0; i < this.inputs.length; i++) {
      this.inputs[i].checked = false;
    }
    if (this.radio) {
      this.radio.value = '';
    }
    this.setInputValue(null);
  };

  SwatchBoundWidget.prototype.setInvalid = function (invalid) {
    for (var i = 0; i < this.inputs.length; i++) {
      if (invalid) {
        this.inputs[i].setAttribute('aria-invalid', 'true');
      } else {
        this.inputs[i].removeAttribute('aria-invalid');
      }
    }
  };

  SwatchBoundWidget.prototype.getTextLabel = function () {
    var input = this.selected();
    if (!input) {
      return null;
    }
    var label = input.closest('label');
    return label ? label.textContent.trim() : input.value;
  };

  SwatchBoundWidget.prototype.focus = function () {
    var input = this.selected() || this.inputs[0];
    if (input && input.focus) {
      input.focus();
    }
  };

  function SwatchSelectDefinition(html) {
    WidgetDefinition.call(this, html);
  }
  SwatchSelectDefinition.prototype = Object.create(WidgetDefinition.prototype);
  SwatchSelectDefinition.prototype.constructor = SwatchSelectDefinition;
  SwatchSelectDefinition.prototype.createBound = function (container, name) {
    return new SwatchBoundWidget(container, name);
  };

  window.telepath.register(
    'wagtail_daisIE.widgets.SwatchSelect',
    SwatchSelectDefinition,
  );
})();
