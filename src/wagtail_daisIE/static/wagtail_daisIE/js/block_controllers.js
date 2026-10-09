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

  window.wagtail.app.register('daisie-image-block', ImageBlockController);
  window.wagtail.app.register('daisie-audience', AudienceController);
  window.wagtail.app.register(
    'daisie-background-layer',
    BackgroundLayerController,
  );
})();
