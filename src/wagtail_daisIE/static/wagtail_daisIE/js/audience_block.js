/**
 * Hide the `audience` field on the block settings panel if the project
 * settings do not define any audience rules.
 */
class AudienceBlockDefinition
  extends window.wagtailStreamField.blocks.StructBlockDefinition
{
  render(placeholder, prefix, initialState, initialError) {
    const block = super.render(placeholder, prefix, initialState, initialError);
    const root =
      (block.container && block.container[0]) || block.element || document;
    const audienceBlock = root.querySelector('[data-contentpath="audience"]');
    if (!audienceBlock) {
      return block;
    }

    const rules = window.WAGTAIL_DAISIE_AUDIENCE_RULES;
    const hasRules =
      rules && typeof rules === 'object' && Object.values(rules).length > 0;
    audienceBlock.style.display = hasRules ? '' : 'none';

    return block;
  }
}
window.telepath.register(
  'wagtail_daisIE.base_blocks.AudienceBlock',
  AudienceBlockDefinition,
);
