/**
 * Ensure that BackgroundLayerBlock only renders fields relevant to the
 * selected layer type.
 * Solid: color
 * Image: image, position, size, repeat
 * Gradient: gradient_shape, gradient_angle, gradient_stops
 */
class BackgroundLayerBlockDefinition
  extends window.wagtailStreamField.blocks.StructBlockDefinition
{
  render(placeholder, prefix, initialState, initialError) {
    const block = super.render(placeholder, prefix, initialState, initialError);
    const root =
      (block.container && block.container[0]) || block.element || document;

    const fieldsByType = {
      solid: ['color'],
      image: ['image', 'position', 'size', 'repeat'],
      gradient: ['gradient_shape', 'gradient_angle', 'gradient_stops'],
    };

    const typeField = root.querySelector(
      '[data-contentpath="layer_type"] select, [data-contentpath="layer_type"] input',
    );
    if (!typeField) {
      return block;
    }

    const hiddenTypes = Object.keys(fieldsByType).filter(
      (type) => type !== typeField.value,
    );
    for (const type of hiddenTypes) {
      for (const field of fieldsByType[type]) {
        const wrapper = root.querySelector(`[data-contentpath="${field}"]`);
        if (wrapper) {
          wrapper.style.display = 'none';
        }
      }
    }

    return block;
  }
}
window.telepath.register(
  'wagtail_daisIE.base_blocks.BackgroundLayerBlock',
  BackgroundLayerBlockDefinition,
);
