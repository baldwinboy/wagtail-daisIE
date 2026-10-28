/**
 * Numeric slider widget (DaisyUINumberSliderWidget).
 *
 * Keeps the range input and the number input in sync in both directions. The
 * number input is the value carrier; an empty value resets the range to its
 * minimum. The redundant numeric readout is dropped (the number input already
 * shows the value).
 *
 * Registered as a Stimulus controller (loaded through the widget's Media).
 */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  class NumberSliderController extends Controller {
    static targets = ['range', 'number'];

    connect() {
      this.rangeTarget_ = this.hasRangeTarget ? this.rangeTarget : null;
      this.numberTarget_ = this.hasNumberTarget ? this.numberTarget : null;

      this.min = this.rangeTarget_
        ? parseInt(this.rangeTarget_.getAttribute('min') || '0', 10)
        : 0;
      this.max = this.rangeTarget_
        ? parseInt(this.rangeTarget_.getAttribute('max') || '100', 10)
        : 100;

      this.onRangeInput = this.handleRangeInput.bind(this);
      this.onNumberInput = this.handleNumberInput.bind(this);

      if (this.rangeTarget_) {
        this.rangeTarget_.addEventListener('input', this.onRangeInput);
      }
      if (this.numberTarget_) {
        this.numberTarget_.addEventListener('input', this.onNumberInput);
        this.numberTarget_.addEventListener('change', this.onNumberInput);
      }

      this.syncFromNumber();
    }

    disconnect() {
      if (this.rangeTarget_) {
        this.rangeTarget_.removeEventListener('input', this.onRangeInput);
      }
      if (this.numberTarget_) {
        this.numberTarget_.removeEventListener('input', this.onNumberInput);
        this.numberTarget_.removeEventListener('change', this.onNumberInput);
      }
    }

    handleRangeInput() {
      if (this.numberTarget_ && this.rangeTarget_) {
        this.numberTarget_.value = this.rangeTarget_.value;
      }
    }

    handleNumberInput() {
      this.syncFromNumber();
    }

    syncFromNumber() {
      var raw = this.numberTarget_ ? this.numberTarget_.value : '';
      var parsed = parseInt(raw, 10);
      if (isNaN(parsed)) {
        if (this.rangeTarget_) {
          this.rangeTarget_.value = this.min;
        }
        return;
      }
      parsed = Math.min(Math.max(parsed, this.min), this.max);
      if (this.numberTarget_ && this.numberTarget_.value !== String(parsed)) {
        this.numberTarget_.value = parsed;
      }
      if (this.rangeTarget_) {
        this.rangeTarget_.value = parsed;
      }
    }
  }

  window.wagtail.app.register('daisie-number-slider', NumberSliderController);
})();
