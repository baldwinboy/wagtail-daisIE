/**
 * Responsive utility editor: design area -> property -> side -> value.
 *
 * The submitted field is the native value select. All options are rendered
 * server-side; this controller only filters the existing option nodes by their
 * ``data-area`` / ``data-property`` / ``data-side`` attributes, then drives the
 * slider. Visibility of the value controls is delegated to Wagtail's ``w-zone``
 * controller via a ``daisie:widget-changed`` event.
 *
 * Without JavaScript the server-rendered selects remain usable.
 */
(function () {
  'use strict';

  var Controller = window.StimulusModule.Controller;

  function rebuild(select, options) {
    var current = select.value;
    while (select.firstChild) {
      select.removeChild(select.firstChild);
    }
    options.forEach(function (option) {
      select.appendChild(option.cloneNode(true));
    });
    if (
      options.some(function (option) {
        return option.value === current;
      })
    ) {
      select.value = current;
    } else if (select.options.length) {
      select.selectedIndex = 0;
    }
  }

  class ResponsiveUtilityController extends Controller {
    static targets = [
      'area',
      'property',
      'side',
      'sideWrapper',
      'value',
      'valueWrapper',
      'slider',
    ];

    connect() {
      if (
        !this.hasAreaTarget ||
        !this.hasPropertyTarget ||
        !this.hasSideTarget ||
        !this.hasValueTarget
      ) {
        return;
      }

      this.propertyOptions = Array.prototype.slice.call(
        this.propertyTarget.options,
      );
      this.sideOptions = Array.prototype.slice.call(this.sideTarget.options);
      this.valueOptions = Array.prototype.slice.call(this.valueTarget.options);

      this.render();

      this.areaTarget.addEventListener(
        'change',
        this.onFilterChange.bind(this),
      );
      this.propertyTarget.addEventListener(
        'change',
        this.onFilterChange.bind(this),
      );
      this.sideTarget.addEventListener(
        'change',
        this.onFilterChange.bind(this),
      );
    }

    selectedProperty() {
      return this.propertyTarget.selectedOptions[0] || null;
    }

    render() {
      var area = this.areaTarget.value;
      rebuild(
        this.propertyTarget,
        this.propertyOptions.filter(function (option) {
          return option.dataset.area === area;
        }),
      );

      var property = this.selectedProperty();
      var widget = property ? property.dataset.widget || 'slider' : 'slider';
      var sideKeys =
        property && property.dataset.sides
          ? property.dataset.sides.split(',')
          : [];

      this.sideWrapperTarget.hidden = sideKeys.length <= 1;
      rebuild(
        this.sideTarget,
        this.sideOptions.filter(function (option) {
          return sideKeys.indexOf(option.value) !== -1;
        }),
      );

      var key = property ? property.value : '';
      var side = this.sideTarget.value || 'all';
      rebuild(
        this.valueTarget,
        this.valueOptions.filter(function (option) {
          return (
            option.dataset.area === area &&
            option.dataset.property === key &&
            option.dataset.side === side
          );
        }),
      );

      window.dispatchEvent(
        new CustomEvent('daisie:widget-changed', {
          detail: {
            slider: widget === 'slider',
            select: widget === 'select',
          },
        }),
      );

      this.refreshSlider();
    }

    /**
     * Delegate slider state to the preset slider controller.
     *
     * The responsive editor and the preset slider share one component; the
     * editor only tells it that the option set changed.
     */
    refreshSlider() {
      var slider = this.application.getControllerForElementAndIdentifier(
        this.element,
        'daisie-preset-slider',
      );
      if (slider) {
        slider.refresh(true);
      }
    }

    onFilterChange() {
      this.render();
    }
  }

  window.wagtail.app.register(
    'daisie-responsive-utility',
    ResponsiveUtilityController,
  );
})();
