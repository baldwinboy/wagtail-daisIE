/**
 * Image block: show only the field relevant to the chosen image source.
 *
 * ``image`` is used for a static image, ``image_expression`` for the
 * ``From context`` source. Mirrors the Wagtail StructBlock render protocol used
 * by audience_block.js.
 *
 * The definition is registered once Wagtail's StreamField/telepath runtime is
 * available, so an unlucky script order cannot throw and leave the whole
 * StreamField widget uninitialised (which strips the hidden ``-count`` input
 * and makes saving fail).
 */
(function () {
  var CONSTRUCTOR = 'wagtail_daisIE.blocks.media.ImageBlock';

  function ready() {
    return (
      window.wagtailStreamField &&
      window.wagtailStreamField.blocks &&
      window.telepath
    );
  }

  function define() {
    class ImageBlockDefinition
      extends window.wagtailStreamField.blocks.StructBlockDefinition
    {
      render(placeholder, prefix, initialState, initialError) {
        const block = super.render(
          placeholder,
          prefix,
          initialState,
          initialError,
        );
        const root =
          (block.container && block.container[0]) || block.element || document;
        const sourceWrap = root.querySelector(
          '[data-contentpath="image_source"]',
        );
        const source = sourceWrap
          ? sourceWrap.querySelector('select, input:not([type="hidden"])')
          : null;
        const imageWrap = root.querySelector('[data-contentpath="image"]');
        const exprWrap = root.querySelector(
          '[data-contentpath="image_expression"]',
        );
        if (!source || (!imageWrap && !exprWrap)) {
          return block;
        }
        const sync = () => {
          const dynamic = source.value === 'dynamic';
          if (imageWrap) {
            imageWrap.style.display = dynamic ? 'none' : '';
          }
          if (exprWrap) {
            exprWrap.style.display = dynamic ? '' : 'none';
          }
        };
        source.addEventListener('change', sync);
        sync();
        return block;
      }
    }
    window.telepath.register(CONSTRUCTOR, ImageBlockDefinition);
  }

  if (ready()) {
    define();
    return;
  }

  var tries = 0;
  var timer = setInterval(function () {
    if (ready()) {
      clearInterval(timer);
      define();
    } else if (++tries > 200) {
      clearInterval(timer);
    }
  }, 25);
})();
