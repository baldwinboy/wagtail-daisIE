/**
 * Keep a Feed's internal name in sync with its display title.
 *
 * The controller is attached to the title input. It fills the internal name
 * with the slugified title until the internal name is edited manually.
 */
(function (root) {
  'use strict';

  function slugify(value) {
    return String(value || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  function attach(source, target) {
    if (!source || !target) {
      return function () {};
    }

    var edited =
      Boolean(target.value) && target.value !== slugify(source.value);

    function sync() {
      if (edited) {
        return;
      }
      var next = slugify(source.value);
      if (next) {
        target.value = next;
      }
    }

    function markEdited() {
      edited = true;
    }

    source.addEventListener('input', sync);
    target.addEventListener('input', markEdited);
    sync();

    return function () {
      source.removeEventListener('input', sync);
      target.removeEventListener('input', markEdited);
    };
  }

  var api = { slugify: slugify, attach: attach };

  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.daisieFeedTitleSlug = api;
  }

  if (!root.StimulusModule || !root.StimulusModule.Controller) {
    return;
  }

  var Controller = root.StimulusModule.Controller;

  class FeedTitleSlugController extends Controller {
    connect() {
      var form = this.element.closest('form');
      this.target = form
        ? form.querySelector('[data-daisie-feed-title-slug-target="name"]')
        : null;
      this.cleanup = attach(this.element, this.target);
    }

    disconnect() {
      if (this.cleanup) {
        this.cleanup();
      }
    }
  }

  root.wagtail.app.register('daisie-feed-title-slug', FeedTitleSlugController);
})(typeof window !== 'undefined' ? window : globalThis);
