/**
 * Toggle background layer field visibility based on layer_type choice.
 * Fields are tagged with CSS classes: layer-solid, layer-gradient, layer-image.
 *
 * Works for both rendering contexts these classes appear in:
 * - model panels (wagtail_daisIE/models/background.py): each FieldPanel carries
 *   its classname on a `.w-field__wrapper` element;
 * - streamfield blocks (wagtail_daisIE/blocks/background.py): each block child
 *   carries its classname on a `[data-field]` element.
 */
(function () {
  var PANEL_SELECTOR = '.layer-solid, .layer-gradient, .layer-image';

  /**
   * Find the element that wraps this layer form's conditional field panels.
   *
   * The panels are never children of the layer_type field itself:
   * - model panels: .background-layer-form and .layer-* are siblings inside
   *   the MultiFieldPanel body (.w-field__wrapper elements);
   * - streamfield blocks: they are siblings inside the struct block root
   *   ([data-contentpath] children of the same struct).
   */
  function findGroupContainer(layerForm) {
    var node = layerForm.parentElement;
    while (node && node.nodeType === Node.ELEMENT_NODE) {
      if (node.querySelector(PANEL_SELECTOR)) return node;
      node = node.parentElement;
    }
    // Fall back to the field itself if the expected structure is missing.
    return layerForm;
  }

  function toggleLayerFields(layerForm) {
    var typeSelect = layerForm.querySelector('select');
    if (!typeSelect) return;
    var layerType = typeSelect.value;
    var group = findGroupContainer(layerForm);

    group.querySelectorAll(PANEL_SELECTOR).forEach(function (panel) {
      // In streamfields each field is wrapped in a div[data-contentpath]
      // (label + widget), so hide that whole block rather than just the
      // [data-field] element. For model panels the .w-field__wrapper itself
      // carries the class, so it is hidden directly.
      var root = panel.closest('[data-contentpath]') || panel;
      var show = panel.classList.contains('layer-' + layerType);
      root.style.display = show ? '' : 'none';
    });
  }

  function initLayerForm(layerForm) {
    // Skip the copy used by the inline formset's empty <template>; it is
    // initialised by the mutation observer once it is cloned in.
    if (layerForm.closest('template')) return;
    if (layerForm.getAttribute('data-layer-form-ready')) return;
    layerForm.setAttribute('data-layer-form-ready', '1');

    var typeSelect = layerForm.querySelector('select');
    if (typeSelect) {
      typeSelect.addEventListener('change', function () {
        toggleLayerFields(layerForm);
      });
      toggleLayerFields(layerForm);
    }
  }

  // Handle existing forms on page load.
  document.querySelectorAll('.background-layer-form').forEach(initLayerForm);

  // Handle newly added inline forms and streamfield blocks.
  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        var layerForm = node.closest && node.closest('.background-layer-form');
        if (!layerForm) {
          layerForm =
            node.querySelector && node.querySelector('.background-layer-form');
        }
        if (layerForm) initLayerForm(layerForm);
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
