/**
 * Shared Telepath render protocol for the DaisyUI admin widgets.
 *
 * Implements the documented Wagtail widget client-side API: splice the
 * server-rendered HTML (with __NAME__/__ID__ tokens) into the DOM and return a
 * bound widget so Telepath can call setState() with the restored value.
 *
 * Exposed as ``window.WAGTAIL_DAISIE.WidgetDefinition`` so the swatch and
 * slider definitions share one implementation instead of duplicating it.
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

  function WidgetDefinition(html) {
    this.html = html;
  }

  WidgetDefinition.prototype.render = function (
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

  window.WAGTAIL_DAISIE = window.WAGTAIL_DAISIE || {};
  window.WAGTAIL_DAISIE.WidgetDefinition = WidgetDefinition;
})();
