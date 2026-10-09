/* Form pages: Stimulus controllers for the "Model to create" hub, the per-field
 * "Model field" selects and the "Fields available to link" help panel.
 *
 * The selects render their options server-side, so the one case that needs a
 * client-side update is a model change (which is not saved yet). Stimulus
 * auto-connects to dynamically added InlinePanel rows through outlets, so no
 * manual DOM scanning or MutationObserver is required. */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  /* Rebuild a select's options: a blank placeholder first (selected when there
   * is no stored value), then the fields, then the stored value as a "(missing)"
   * option when it is no longer available. */
  function buildOptions(select, fields, emptyLabel) {
    var current = select.value;
    select.innerHTML = '';

    var blank = document.createElement('option');
    blank.value = '';
    blank.textContent = emptyLabel || '';
    if (!current) {
      blank.selected = true;
    }
    select.appendChild(blank);

    var known = !current;
    fields.forEach(function (field) {
      var option = document.createElement('option');
      option.value = field.name;
      option.textContent = field.label || field.name;
      if (field.name === current) {
        option.selected = true;
        known = true;
      }
      select.appendChild(option);
    });

    if (!known) {
      var stale = document.createElement('option');
      stale.value = current;
      stale.textContent = current + ' (missing)';
      stale.selected = true;
      select.appendChild(stale);
    }
  }

  function fieldsFor(contextModels, key) {
    var meta = contextModels[key];
    return (meta && meta.fields) || [];
  }

  class ModelFieldController extends Controller {
    static values = { empty: String };

    setFields(fields) {
      buildOptions(this.element, fields, this.emptyValue);
    }
  }

  class InstanceModelController extends Controller {
    static values = { contextModels: Object };

    static outlets = ['daisie-form-model-field'];

    refresh() {
      var fields = fieldsFor(this.contextModelsValue, this.element.value);
      this.daisieFormModelFieldOutlets.forEach(function (outlet) {
        outlet.setFields(fields);
      });
      this.renderHelp(fields);
    }

    daisieFormModelFieldOutletConnected() {
      this.refresh();
    }

    /* Keep the "Fields available to link" panel in sync with the chosen model.
     * The panel is server-rendered for the saved model; its table body is
     * rebuilt here on change (values are set as text, never innerHTML). */
    renderHelp(fields) {
      var panel = document.querySelector('[data-daisie-model-fields]');
      if (!panel) {
        return;
      }
      var body = panel.querySelector('[data-daisie-model-fields-body]');
      var empty = panel.querySelector('[data-daisie-model-fields-empty]');
      if (body) {
        body.textContent = '';
        fields.forEach(function (field) {
          var row = document.createElement('tr');
          var name = document.createElement('td');
          var code = document.createElement('code');
          code.textContent = field.name;
          name.appendChild(code);
          var label = document.createElement('td');
          label.textContent = field.label || '';
          row.appendChild(name);
          row.appendChild(label);
          body.appendChild(row);
        });
      }
      if (empty) {
        empty.hidden = fields.length > 0;
      }
    }
  }

  window.wagtail.app.register('daisie-form-model-field', ModelFieldController);
  window.wagtail.app.register(
    'daisie-form-instance-model',
    InstanceModelController,
  );
})();
