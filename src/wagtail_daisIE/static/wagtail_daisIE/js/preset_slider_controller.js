/**
 * Preset (semantic) slider widget (DaisyUISliderWidget).
 *
 * The range slider covers every option so any value can be reached by
 * scrubbing; the semantic values (None, Auto, Fit, Max, ...) are also exposed
 * as a keyboard-accessible button group for quick access. Both controls write
 * to the hidden <select> value carrier.
 *
 * Registered as a Stimulus controller (loaded through the widget's Media).
 */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  var AUTO_PREFIXES = [
    'm-',
    'mx-',
    'my-',
    'mt-',
    'mr-',
    'mb-',
    'ml-',
    'w-',
    'h-',
    'size-',
    'min-w-',
    'min-h-',
    'max-w-',
    'max-h-',
  ];

  function isSemantic(value, option) {
    if (option && option.dataset && option.dataset.semantic === '1') {
      return true;
    }
    if (value === '' || value === 'auto') {
      return true;
    }
    for (var i = 0; i < AUTO_PREFIXES.length; i++) {
      if (value === AUTO_PREFIXES[i] + 'auto') {
        return true;
      }
    }
    var suffix = String(value).split('-').pop();
    return (
      [
        'full',
        'min',
        'max',
        'fit',
        'screen',
        'dvw',
        'dvh',
        'lvw',
        'lvh',
        'svw',
        'svh',
      ].indexOf(suffix) !== -1
    );
  }

  class PresetSliderController extends Controller {
    static targets = ['select', 'range', 'value'];

    connect() {
      this.selectTarget_ = this.hasSelectTarget ? this.selectTarget : null;
      this.rangeTarget_ = this.hasRangeTarget ? this.rangeTarget : null;
      this.valueTarget_ = this.hasValueTarget ? this.valueTarget : null;

      this.allValues = [];
      this.allTexts = [];
      if (this.selectTarget_) {
        Array.prototype.forEach.call(
          this.selectTarget_.options,
          function (opt) {
            this.allValues.push(opt.value);
            this.allTexts.push(opt.text);
          }.bind(this),
        );
      }

      this.onRangeInput = this.handleRangeInput.bind(this);
      if (this.rangeTarget_) {
        this.rangeTarget_.addEventListener('input', this.onRangeInput);
      }

      var buttons = this.element.querySelectorAll(
        '[data-daisie-preset-semantic]',
      );
      Array.prototype.forEach.call(
        buttons,
        function (btn) {
          btn.addEventListener(
            'click',
            function () {
              this.selectSemantic(btn.getAttribute('data-value') || '');
            }.bind(this),
          );
        }.bind(this),
      );

      this.syncFromSelect();
    }

    disconnect() {
      if (this.rangeTarget_) {
        this.rangeTarget_.removeEventListener('input', this.onRangeInput);
      }
    }

    syncFromSelect() {
      if (!this.selectTarget_) return;
      var value = this.selectTarget_.value;
      var option = this.findOption(value);
      var isSem = option ? isSemantic(option.value, option) : false;

      var buttons = this.element.querySelectorAll(
        '[data-daisie-preset-semantic]',
      );
      Array.prototype.forEach.call(buttons, function (btn) {
        btn.setAttribute(
          'aria-pressed',
          String(btn.getAttribute('data-value') === value && isSem),
        );
      });

      var idx = this.allValues.indexOf(String(value));
      if (idx === -1) idx = 0;
      if (this.rangeTarget_) {
        this.rangeTarget_.value = idx;
      }
      var text = option ? option.text : value;
      this.updateReadout(text);
      if (this.rangeTarget_) {
        this.rangeTarget_.setAttribute('aria-valuetext', text || '');
      }
    }

    selectSemantic(value) {
      if (this.selectTarget_) {
        this.selectTarget_.value = value;
      }
      this.syncFromSelect();
      if (this.selectTarget_) {
        this.selectTarget_.dispatchEvent(
          new Event('change', { bubbles: true }),
        );
      }
    }

    handleRangeInput() {
      if (!this.rangeTarget_ || !this.selectTarget_) return;
      var idx = parseInt(this.rangeTarget_.value, 10) || 0;
      idx = Math.min(Math.max(idx, 0), this.allValues.length - 1);
      var value = this.allValues[idx];
      if (value !== undefined) {
        this.selectTarget_.value = value;
      }
      var buttons = this.element.querySelectorAll(
        '[data-daisie-preset-semantic]',
      );
      Array.prototype.forEach.call(buttons, function (btn) {
        btn.setAttribute('aria-pressed', 'false');
      });
      this.updateReadout(this.allTexts[idx] || value);
      if (this.rangeTarget_) {
        this.rangeTarget_.setAttribute(
          'aria-valuetext',
          this.allTexts[idx] || value || '',
        );
      }
      if (this.selectTarget_) {
        this.selectTarget_.dispatchEvent(
          new Event('change', { bubbles: true }),
        );
      }
    }

    findOption(value) {
      if (!this.selectTarget_) return null;
      for (var i = 0; i < this.selectTarget_.options.length; i++) {
        var opt = this.selectTarget_.options[i];
        if (opt.value === String(value)) return opt;
      }
      return null;
    }

    updateReadout(text) {
      if (this.valueTarget_) {
        this.valueTarget_.textContent = text || '';
      }
    }
  }

  window.wagtail.app.register('daisie-preset-slider', PresetSliderController);
})();
