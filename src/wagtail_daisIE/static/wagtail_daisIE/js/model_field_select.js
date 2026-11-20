(function (root) {
  'use strict';

  function createOption(value, label) {
    var option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    return option;
  }

  function ModelFieldSelectController() {}

  ModelFieldSelectController.prototype.connect = function () {
    var select = this.element;
    var form = select.closest('form');
    var modelSelect = null;
    if (form) {
      modelSelect =
        form.querySelector('select[name="instance_model"]') ||
        form.querySelector('select[name$="-instance_model"]');
    }
    if (!modelSelect) {
      return;
    }
    this.modelSelect = modelSelect;
    this.onChange = this.sync.bind(this);
    modelSelect.addEventListener('change', this.onChange);
    this.sync();
  };

  ModelFieldSelectController.prototype.disconnect = function () {
    if (this.modelSelect) {
      this.modelSelect.removeEventListener('change', this.onChange);
    }
  };

  ModelFieldSelectController.prototype.sync = function () {
    var select = this.element;
    var modelSelect = this.modelSelect;
    if (!select || !modelSelect) {
      return;
    }
    var state =
      (root.WAGTAIL_DAISIE_CONTEXT_MODELS || {})[modelSelect.value] || {};
    var fields = state.formFields || [];
    var current = select.value;
    var emptyLabel = select.getAttribute('data-daisie-model-field-empty-label') || '';
    select.innerHTML = '';
    var blank = document.createElement('option');
    blank.value = '';
    blank.textContent = emptyLabel || '---------';
    select.appendChild(blank);
    fields.forEach(function (field) {
      select.appendChild(createOption(field.name, field.label || field.name));
    });
    if (fields.some(function (field) {
      return field.name === current;
    })) {
      select.value = current;
    } else {
      select.value = '';
    }
  };

  if (root.StimulusModule && root.StimulusModule.Controller) {
    var Controller = root.StimulusModule.Controller;
    function BoundController() {
      Controller.apply(this, arguments);
    }
    BoundController.prototype = Object.create(Controller.prototype);
    BoundController.prototype.connect = ModelFieldSelectController.prototype.connect;
    BoundController.prototype.disconnect = ModelFieldSelectController.prototype.disconnect;
    BoundController.prototype.sync = ModelFieldSelectController.prototype.sync;
    root.wagtail.app.register('daisie-model-field-select', BoundController);
  }
})(typeof window !== 'undefined' ? window : globalThis);
