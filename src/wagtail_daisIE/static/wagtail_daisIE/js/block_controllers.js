/**
 * Stimulus controllers for DaisyUI StructBlock admin behaviour.
 *
 * Registered globally (via ``insert_global_admin_js``) so they initialise for
 * blocks added dynamically inside StreamFields and inline panels without any
 * manual DOM scanning or telepath widget definitions.
 */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  function contentPath(root, name) {
    return root.querySelector('[data-contentpath="' + name + '"]');
  }

  /**
   * Image block: show only the field relevant to the chosen image source.
   * ``image`` is used for a static image, ``image_expression`` for the
   * "From context" source.
   */
  class ImageBlockController extends Controller {
    connect() {
      this.sourceWrap = contentPath(this.element, 'image_source');
      this.imageWrap = contentPath(this.element, 'image');
      this.expressionWrap = contentPath(this.element, 'image_expression');
      this.source = this.sourceWrap
        ? this.sourceWrap.querySelector('select, input:not([type="hidden"])')
        : null;
      if (!this.source || (!this.imageWrap && !this.expressionWrap)) {
        return;
      }
      this.onChange = this.sync.bind(this);
      this.source.addEventListener('change', this.onChange);
      this.sync();
    }

    disconnect() {
      if (this.source) {
        this.source.removeEventListener('change', this.onChange);
      }
    }

    sync() {
      var dynamic = this.source.value === 'dynamic';
      if (this.imageWrap) {
        this.imageWrap.style.display = dynamic ? 'none' : '';
      }
      if (this.expressionWrap) {
        this.expressionWrap.style.display = dynamic ? '' : 'none';
      }
    }
  }

  /**
   * Audience block: hide the ``audience`` field when the project settings do
   * not define any audience rules.
   */
  class AudienceController extends Controller {
    connect() {
      var audience = contentPath(this.element, 'audience');
      if (!audience) {
        return;
      }
      var rules = window.WAGTAIL_DAISIE_AUDIENCE_RULES;
      var hasRules =
        rules && typeof rules === 'object' && Object.values(rules).length > 0;
      audience.style.display = hasRules ? '' : 'none';
    }
  }

  /**
   * Background layer: toggle the layer-specific field groups (tagged
   * ``.layer-solid`` / ``.layer-gradient`` / ``.layer-image``) based on the
   * selected ``layer_type``.
   *
   * Works for StreamField blocks (the ``layer_type`` select inside the struct)
   * and the theme's inline background-layer panel. The controller element is
   * the ``layer_type`` select; the field groups are found by walking up to the
   * nearest ancestor that contains them.
   */
  class BackgroundLayerController extends Controller {
    connect() {
      this.select = this.element.matches('select')
        ? this.element
        : this.element.querySelector('.background-layer-form select, select');
      if (!this.select) {
        return;
      }
      this.group = this.findGroup();
      this.onChange = this.sync.bind(this);
      this.select.addEventListener('change', this.onChange);
      this.sync();
    }

    disconnect() {
      if (this.select) {
        this.select.removeEventListener('change', this.onChange);
      }
    }

    findGroup() {
      var node = this.select.parentElement;
      while (node && node !== document.body) {
        if (node.querySelector('.layer-solid, .layer-gradient, .layer-image')) {
          return node;
        }
        node = node.parentElement;
      }
      return this.element;
    }

    sync() {
      var type = this.select.value;
      this.group
        .querySelectorAll('.layer-solid, .layer-gradient, .layer-image')
        .forEach(function (panel) {
          var root = panel.closest('[data-contentpath]') || panel;
          root.style.display = panel.classList.contains('layer-' + type)
            ? ''
            : 'none';
        });
    }
  }

  function control(target, selector) {
    if (!target) {
      return null;
    }
    return target.matches(selector) ? target : target.querySelector(selector);
  }

  function setTargetState(target, visible, disabled, disableWhenHidden) {
    if (!target) {
      return;
    }
    target.hidden = !visible;
    var shouldDisable = disabled || (!visible && disableWhenHidden !== false);
    var controls = target.matches('input, select, textarea, button')
      ? [target]
      : target.querySelectorAll('input, select, textarea, button');
    controls.forEach(function (field) {
      field.disabled = shouldDisable;
    });
  }

  /**
   * Context condition builder: narrow the property list to the chosen context
   * model and adapt the value input to the property type.
   */
  class VisibilityConditionController extends Controller {
    static targets = [
      'contextModel',
      'fieldName',
      'operator',
      'compareValue',
      'rule',
      'expression',
    ];

    connect() {
      this.hasFields = true;
      this.refreshFields(true);
      this.refreshValue();
      this.applyVisibility();
    }

    modelSelect() {
      return control(
        this.hasContextModelTarget ? this.contextModelTarget : null,
        'select',
      );
    }

    fieldSelect() {
      return control(
        this.hasFieldNameTarget ? this.fieldNameTarget : null,
        'select',
      );
    }

    operatorSelect() {
      return control(
        this.hasOperatorTarget ? this.operatorTarget : null,
        'select',
      );
    }

    valueInput() {
      return control(
        this.hasCompareValueTarget ? this.compareValueTarget : null,
        'input, textarea',
      );
    }

    expressionInput() {
      return control(
        this.hasExpressionTarget ? this.expressionTarget : null,
        'input, textarea',
      );
    }

    refresh(event) {
      var target = event ? event.target : null;
      if (
        target &&
        this.hasContextModelTarget &&
        this.contextModelTarget.contains(target)
      ) {
        this.refreshFields(true);
      }
      if (
        target &&
        this.hasFieldNameTarget &&
        this.fieldNameTarget.contains(target)
      ) {
        this.refreshValue();
        this.applyBooleanDefault();
      } else if (
        target &&
        ((this.hasOperatorTarget && this.operatorTarget.contains(target)) ||
          (this.hasExpressionTarget &&
            this.expressionTarget.contains(target)) ||
          (this.hasRuleTarget && this.ruleTarget.contains(target)))
      ) {
        this.refreshValue();
      }
      this.applyVisibility();
    }

    models() {
      return window.WAGTAIL_DAISIE_CONTEXT_MODELS || {};
    }

    currentFields() {
      var model = this.modelSelect();
      if (!model || !model.value) {
        return [];
      }
      var state = this.models()[model.value];
      return state && state.fields ? state.fields : [];
    }

    selectedField() {
      var select = this.fieldSelect();
      if (!select || !select.value) {
        return null;
      }
      return (
        this.currentFields().find((item) => item.name === select.value) || null
      );
    }

    refreshFields(preserve) {
      var select = this.fieldSelect();
      if (!select || !window.WAGTAIL_DAISIE_CONTEXT_MODELS) {
        return;
      }
      var model = this.modelSelect();
      var fields = this.currentFields();
      var current = preserve && select.value ? select.value : '';
      select.innerHTML = '';
      var blank = document.createElement('option');
      blank.value = '';
      blank.textContent = 'Choose a property…';
      select.appendChild(blank);
      fields.forEach(function (field) {
        var option = document.createElement('option');
        option.value = field.name;
        option.textContent = field.label;
        select.appendChild(option);
      });
      if (
        fields.some(function (field) {
          return field.name === current;
        })
      ) {
        select.value = current;
      }
      this.hasFields = fields.length > 0;
      select.disabled = !model || !model.value || !this.hasFields;
    }

    refreshValue() {
      var input = this.valueInput();
      var field = this.selectedField();
      if (!input) {
        return;
      }
      var type = field && field.type ? field.type : '';
      var operator = this.operatorSelect();
      var operatorValue = operator ? operator.value : '';
      var inputType = 'text';
      if (['in', 'not_in'].includes(operatorValue)) {
        inputType = 'text';
      } else if (
        [
          'IntegerField',
          'BigIntegerField',
          'SmallIntegerField',
          'PositiveIntegerField',
          'PositiveSmallIntegerField',
          'FloatField',
          'DecimalField',
        ].includes(type)
      ) {
        inputType = 'number';
      } else if (type === 'DateField') {
        inputType = 'date';
      } else if (type === 'DateTimeField') {
        inputType = 'datetime-local';
      }
      input.type = inputType;

      var list = this.element.querySelector(
        'datalist[data-daisie-visibility-choices]',
      );
      if (field && field.choices && field.choices.length) {
        if (!list) {
          list = document.createElement('datalist');
          list.dataset.daisieVisibilityChoices = '';
          this.element.appendChild(list);
        }
        list.id = input.id + '-choices';
        list.innerHTML = '';
        field.choices.forEach(function (choice) {
          var option = document.createElement('option');
          option.value = choice.value;
          option.label = choice.label;
          list.appendChild(option);
        });
        input.setAttribute('list', list.id);
      } else {
        input.removeAttribute('list');
        if (list) {
          list.remove();
        }
      }
    }

    applyBooleanDefault() {
      var field = this.selectedField();
      var operator = this.operatorSelect();
      if (
        field &&
        operator &&
        ['BooleanField', 'NullBooleanField'].includes(field.type) &&
        !['is_true', 'is_false', 'custom'].includes(operator.value)
      ) {
        operator.value = 'is_true';
      }
    }

    applyVisibility() {
      var model = this.modelSelect();
      var field = this.fieldSelect();
      var operator = this.operatorSelect();
      var expression = this.expressionInput();
      var operatorValue = operator ? operator.value : '';
      var isCustom = operatorValue === 'custom';
      var needsValue = !['', 'is_true', 'is_false', 'custom'].includes(
        operatorValue,
      );
      var pickerActive =
        (model && model.value.trim() !== '') ||
        (field && field.value.trim() !== '');
      var expressionActive =
        !pickerActive && expression && expression.value.trim() !== '';
      var disablePicker = isCustom || expressionActive;

      setTargetState(
        this.hasContextModelTarget ? this.contextModelTarget : null,
        !disablePicker,
        false,
      );
      setTargetState(
        this.hasFieldNameTarget ? this.fieldNameTarget : null,
        !disablePicker,
        !(model && model.value) || !this.hasFields,
      );
      // The operator is needed for an advanced expression; hide it without
      // disabling it so the saved comparison still submits.
      setTargetState(
        this.hasOperatorTarget ? this.operatorTarget : null,
        !expressionActive,
        false,
        false,
      );
      setTargetState(
        this.hasCompareValueTarget ? this.compareValueTarget : null,
        !isCustom && needsValue && !expressionActive,
        false,
      );
      setTargetState(
        this.hasRuleTarget ? this.ruleTarget : null,
        isCustom && !expressionActive,
        false,
      );
      setTargetState(
        this.hasExpressionTarget ? this.expressionTarget : null,
        !pickerActive && !isCustom,
        false,
      );
    }
  }

  /**
   * Populate a target's control-key suggestions from switch blocks in the same
   * admin form. Validation remains server-side.
   */
  class SwitchKeyController extends Controller {
    static targets = ['switchKey'];

    connect() {
      this.refresh();
    }

    refresh(event) {
      var input = control(
        this.hasSwitchKeyTarget ? this.switchKeyTarget : null,
        'input',
      );
      if (!input) {
        return;
      }
      if (
        event &&
        event.target !== input &&
        !event.target.matches('input[name$="-logic_key"]')
      ) {
        return;
      }
      var list = this.element.querySelector(
        'datalist[data-daisie-switch-keys]',
      );
      if (!list) {
        list = document.createElement('datalist');
        list.dataset.daisieSwitchKeys = '';
        this.element.appendChild(list);
      }
      list.id = input.id + '-keys';
      list.innerHTML = '';
      var form = this.element.closest('form') || document;
      form
        .querySelectorAll('input[name$="-logic_key"]')
        .forEach(function (logicInput) {
          var key = logicInput.value.trim();
          if (!key) {
            return;
          }
          var option = document.createElement('option');
          option.value = key;
          option.label = key;
          list.appendChild(option);
        });
      input.setAttribute('list', list.id);
    }
  }

  window.wagtail.app.register('daisie-image-block', ImageBlockController);
  window.wagtail.app.register('daisie-audience', AudienceController);
  window.wagtail.app.register(
    'daisie-background-layer',
    BackgroundLayerController,
  );
  window.wagtail.app.register(
    'daisie-visibility-condition',
    VisibilityConditionController,
  );
  window.wagtail.app.register('daisie-switch-key', SwitchKeyController);
})();
