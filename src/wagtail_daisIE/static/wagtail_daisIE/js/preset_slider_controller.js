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
    static targets = ['select', 'range', 'value', 'semantics'];

    connect() {
      this.selectTarget_ = this.hasSelectTarget ? this.selectTarget : null;
      this.rangeTarget_ = this.hasRangeTarget ? this.rangeTarget : null;
      this.valueTarget_ = this.hasValueTarget ? this.valueTarget : null;

      var needsSemantics =
        this.hasSemanticsTarget && this.semanticsTarget.children.length === 0;
      this.refresh(needsSemantics);

      this.onRangeInput = this.handleRangeInput.bind(this);
      if (this.rangeTarget_) {
        this.rangeTarget_.addEventListener('input', this.onRangeInput);
      }

      this.onSemanticChange = this.onSemanticChange.bind(this);
      if (this.hasSemanticsTarget) {
        this.semanticsTarget.addEventListener('change', this.onSemanticChange);
      }

      this.syncFromSelect();
    }

    /**
     * Re-cache the options and refresh the range/readout.
     *
     * ``rebuildSemantics`` is used by the responsive editor, whose value
     * options change when the editor changes property or side. The design
     * sliders keep their server-rendered buttons.
     */
    refresh(rebuildSemantics) {
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
      if (this.rangeTarget_) {
        this.rangeTarget_.max = String(Math.max(0, this.allValues.length - 1));
      }
      if (rebuildSemantics) {
        this.rebuildSemantics();
      }
      this.syncFromSelect();
    }

    rebuildSemantics() {
      if (!this.hasSemanticsTarget) return;

      while (this.semanticsTarget.firstChild) {
        this.semanticsTarget.removeChild(this.semanticsTarget.firstChild);
      }

      var radioName =
        (this.selectTarget_.name || this.selectTarget_.id) + '-preset';

      Array.prototype.forEach.call(
        this.selectTarget_.options,
        function (option) {
          if (!isSemantic(option.value, option)) return;
          var label = document.createElement('label');
          label.className = 'daisyui-slider-semantic';

          var input = document.createElement('input');
          input.type = 'radio';
          input.className = 'w-sr-only';
          input.name = radioName;
          input.value = option.value;

          var text = document.createElement('span');
          text.textContent = option.text;

          label.appendChild(input);
          label.appendChild(text);
          this.semanticsTarget.appendChild(label);
        }.bind(this),
      );
    }

    disconnect() {
      if (this.rangeTarget_) {
        this.rangeTarget_.removeEventListener('input', this.onRangeInput);
      }
      if (this.hasSemanticsTarget) {
        this.semanticsTarget.removeEventListener(
          'change',
          this.onSemanticChange,
        );
      }
    }

    syncFromSelect() {
      if (!this.selectTarget_) return;
      var value = this.selectTarget_.value;
      var option = this.findOption(value);

      if (this.hasSemanticsTarget) {
        this.semanticsTarget
          .querySelectorAll('input[type="radio"]')
          .forEach(function (input) {
            input.checked = input.value === value;
          });
      }

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

    onSemanticChange(event) {
      if (!event.target.matches('input[type="radio"]')) return;
      this.selectSemantic(event.target.value);
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
      this.syncFromSelect();
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
