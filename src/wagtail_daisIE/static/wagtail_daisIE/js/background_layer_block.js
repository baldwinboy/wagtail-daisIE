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

    const fieldsByType = {
      solid: ['color'],
      image: ['image', 'position', 'size', 'repeat'],
      gradient: ['gradient_shape', 'gradient_angle', 'gradient_stops'],
    };

    const layerTypeField = document.getElementById(prefix + '-layer_type');
    const layerType = layerTypeField.value;
    const notLayerTypes = Object.keys(fieldsByType).filter(
      (type) => type !== layerType,
    );

    for (const fieldName of notLayerTypes) {
      for (const field of fieldsByType[fieldName]) {
        const fieldElement = document.getElementById(prefix + '-' + field);
        fieldElement.style.display = 'block';
      }
    }

    for (const fieldName of notLayerTypes) {
      for (const field of fieldsByType[fieldName]) {
        const fieldElement = document.getElementById(prefix + '-' + field);
        fieldElement.style.display = 'none';
      }
    }

    return block;
  }
}
window.telepath.register(
  'wagtail_daisIE.base_blocks.BackgroundLayerBlock',
  BackgroundLayerBlockDefinition,
);
