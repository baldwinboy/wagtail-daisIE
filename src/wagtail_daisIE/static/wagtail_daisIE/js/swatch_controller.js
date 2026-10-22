/**
 * Colour swatch widget (DaisyUISwatchWidget / DaisyUIRawSwatchWidget).
 *
 * Drives the Coloris inline picker for the widget's "Custom" tile. Registered
 * as a Stimulus controller (loaded through the widget's Media) so it
 * initialises for widgets added dynamically inside StreamFields and inline
 * panels without any manual DOM scanning. Value/state mapping lives in
 * swatch_definition.js; this controller owns only the picker interaction and
 * the custom chip's visual state.
 *
 * Coloris keeps a single physical picker, so only one swatch widget can be
 * active at a time.
 */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  var activeSwatch = null;

  class SwatchController extends Controller {
    static targets = ['output', 'input', 'radio'];
    static values = { colorisOptions: Object, prefix: String };

    connect() {
      this.bound = false;
      // Render the restored custom chip; the telepath bound widget has already
      // synchronously restored the input value by the time Stimulus connects.
      this.syncChip();
    }

    disconnect() {
      if (activeSwatch === this) {
        this.deactivateInline();
      }
    }

    isActive() {
      return activeSwatch === this;
    }

    cleanColor(color) {
      var match = /^#?([0-9a-fA-F]{3,8})$/.exec((color || '').trim());
      return match ? match[1] : null;
    }

    getCurrentColor() {
      if (!this.hasInputTarget) {
        return '';
      }
      var trimmed = (this.inputTarget.value || '').trim();
      if (!trimmed) {
        return '';
      }
      var cleaned = this.cleanColor(trimmed);
      return cleaned ? '#' + cleaned : '';
    }

    /**
     * Render the custom chip from the current custom value. The checkered
     * background (CSS `.daisyui-swatch-chip--custom`) is shown when empty and
     * removed once a colour is set.
     */
    syncChip(color) {
      if (!this.hasOutputTarget) {
        return;
      }
      var value = color === undefined ? this.getCurrentColor() : color;
      this.outputTarget.style.backgroundColor = value;
      this.outputTarget.style.backgroundImage = value ? 'none' : '';
    }

    // Actions ---------------------------------------------------------------

    toggleInline(event) {
      if (event.target === this.inputTarget) return;
      event.preventDefault();
      this.radioTarget.checked = true;
      if (this.isActive()) {
        this.deactivateInline();
      } else {
        this.activateInline();
      }
    }

    activateFromFocus() {
      this.radioTarget.checked = true;
      this.activateInline();
    }

    // Selecting a preset swatch dismisses the inline picker.
    dismissPicker(event) {
      if (event.target && event.target.checked) {
        this.deactivateInline();
      }
    }

    // Map the typed/picked hex back onto the custom radio and update the chip.
    syncFromInput() {
      var color = this.getCurrentColor();
      if (!color) {
        this.radioTarget.value = '';
        this.syncChip('');
        return;
      }
      var isRaw = this.radioTarget.dataset.raw === 'true';
      this.radioTarget.value = isRaw
        ? color
        : this.prefixValue + '-[' + color + ']';
      this.radioTarget.checked = true;
      this.syncChip(color);
      this.radioTarget.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Document-scoped actions (see data-action="...@document" in the template).
    onColorisPick(event) {
      if (!this.isActive() || !event.detail || !event.detail.color) return;
      var color = this.cleanColor(event.detail.color);
      if (!color) return;
      this.inputTarget.value = '#' + color;
      this.inputTarget.dispatchEvent(new Event('input', { bubbles: true }));
    }

    onOutsideClick(event) {
      if (!this.isActive()) return;
      if (this.element.contains(event.target)) return;
      this.deactivateInline();
    }

    // Coloris lifecycle -----------------------------------------------------

    activateInline() {
      if (this.isActive()) return;
      var options = this.colorisOptionsValue || {};
      var config = {
        parent: options.parent || 'body',
        defaultColor: this.getCurrentColor() || '#ffffff',
        swatches: options.swatches || [],
        swatchesOnly: options.swatchesOnly || false,
        format: options.format || 'hex',
        alpha: options.alpha || false,
        inline: true,
      };
      if (!this.bound) {
        // Bind the field only the first time the custom tile is activated;
        // re-applying `el` on later activations would rebind listeners. The
        // widget renders its own colour chip, so skip Coloris's wrapping too.
        config.el = this.inputTarget;
        config.wrap = false;
        this.bound = true;
      }
      try {
        Coloris(config);
      } catch (_e) {
        return;
      }
      activeSwatch = this;

      // The settings panel can still be settling when the picker is first
      // shown, which leaves Coloris with stale/zero colour-area geometry.
      // Re-measure once the layout has settled.
      if (window.requestAnimationFrame) {
        window.requestAnimationFrame(function () {
          try {
            Coloris.updatePosition();
          } catch (_e) {
            /* ignore */
          }
        });
      }
    }

    deactivateInline() {
      // Coloris exposes one physical picker, so turning it off always clears
      // the active controller (even when a preset on another swatch is used).
      activeSwatch = null;
      try {
        Coloris({ inline: false });
      } catch (_e) {
        /* ignore */
      }
    }
  }

  window.wagtail.app.register('daisie-swatch', SwatchController);
})();
