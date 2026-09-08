/**
 * Hide the `audience` field on the block settings panel if the project
 * settings do not define any audience rules.
 */
class AudienceBlockDefinition
  extends window.wagtailStreamField.blocks.StructBlockDefinition
{
  render(placeholder, prefix, initialState, initialError) {
    const block = super.render(placeholder, prefix, initialState, initialError);
    const audienceRules = window.WAGTAIL_DAISIE_AUDIENCE_RULES;
    const audienceBlock = document
      .getElementById(`block_group-${prefix}-section`)
      .closest('[data-contentpath]');
    const hasAudienceRules =
      audienceRules &&
      typeof audienceRules === 'object' &&
      Object.values(audienceRules).length > 0;
    if (!hasAudienceRules) {
      audienceBlock.style.display = 'none';
    } else {
      audienceBlock.style.display = 'block';
    }

    return block;
  }
}
window.telepath.register(
  'wagtail_daisIE.base_blocks.AudienceBlock',
  AudienceBlockDefinition,
);
