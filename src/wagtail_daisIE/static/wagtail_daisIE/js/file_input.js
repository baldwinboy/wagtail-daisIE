/**
 * Progressive enhancement for the file-upload widgets.
 *
 * The native <input type="file"> is always rendered and still submits without
 * JavaScript. This script previews newly selected files and lets a selection be
 * edited before submit. It is intentionally vanilla (no Stimulus) so it works
 * on standalone form pages, and idempotent so the widget and a block can both
 * load it.
 */
(function () {
  'use strict';

  if (window.__daisieFileInputLoaded) {
    return;
  }
  window.__daisieFileInputLoaded = true;

  var initialized = new WeakSet();

  function extension(name) {
    var index = (name || '').lastIndexOf('.');
    return index > -1 ? name.slice(index + 1).toUpperCase() : '';
  }

  function isImage(file) {
    return !!file && !!file.type && file.type.indexOf('image/') === 0;
  }

  function toDataTransfer(files) {
    var transfer = new DataTransfer();
    files.forEach(function (file) {
      transfer.items.add(file);
    });
    return transfer;
  }

  function initAttachments(root) {
    var input = root.querySelector('input[type="file"]');
    var preview = root.querySelector('[data-daisie-file-preview]');
    var template = root.querySelector('template[data-daisie-file-template]');
    if (!input || !preview || !template) {
      return;
    }

    var selected = Array.prototype.slice.call(input.files || []);
    var objectUrls = [];

    function releaseUrls() {
      objectUrls.forEach(function (url) {
        URL.revokeObjectURL(url);
      });
      objectUrls = [];
    }

    function applySelection() {
      if (typeof DataTransfer !== 'function') {
        return;
      }
      try {
        input.files = toDataTransfer(selected).files;
      } catch (error) {
        /* input.files is read-only in some browsers */
      }
    }

    function render() {
      releaseUrls();
      preview.replaceChildren();
      selected.forEach(function (file, index) {
        var fragment = template.content.cloneNode(true);
        var item = fragment.querySelector('[data-daisie-file-item]');
        var nameEl = item.querySelector('[data-daisie-file-name]');
        var iconEl = item.querySelector('[data-daisie-file-icon]');
        nameEl.textContent = file.name;
        if (isImage(file)) {
          var url = URL.createObjectURL(file);
          objectUrls.push(url);
          iconEl.classList.add('daisie-file-attachments__icon--image');
          iconEl.style.backgroundImage = 'url("' + url + '")';
        } else {
          iconEl.textContent = extension(file.name);
        }
        item
          .querySelector('[data-daisie-file-remove]')
          .addEventListener('click', function () {
            selected.splice(index, 1);
            applySelection();
            render();
          });
        preview.appendChild(fragment);
      });
    }

    root
      .querySelectorAll('[data-daisie-file-existing] [data-daisie-file-remove]')
      .forEach(function (button) {
        button.addEventListener('click', function () {
          var item = button.closest('[data-daisie-file-item]');
          if (item) {
            item.remove();
          }
        });
      });

    input.addEventListener('change', function () {
      selected = Array.prototype.slice.call(input.files || []);
      render();
    });

    root.classList.add('daisie-file-attachments--ready');
  }

  function initImage(root) {
    var input = root.querySelector('input[type="file"]');
    var preview = root.querySelector('[data-daisie-file-image-preview]');
    if (!input || !preview) {
      return;
    }
    var objectUrl = null;
    root.classList.add('daisie-file-image--ready');

    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file || !isImage(file)) {
        return;
      }
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
      objectUrl = URL.createObjectURL(file);
      preview.replaceChildren();
      var image = document.createElement('img');
      image.src = objectUrl;
      image.alt = '';
      preview.appendChild(image);
      root.classList.add('daisie-file-image--has-value');
    });
  }

  function init(root) {
    if (initialized.has(root)) {
      return;
    }
    initialized.add(root);
    if (root.matches('[data-daisie-file-attachments]')) {
      initAttachments(root);
    }
    if (root.matches('[data-daisie-file-image]')) {
      initImage(root);
    }
  }

  function scan(scope) {
    if (!scope || !scope.querySelectorAll) {
      return;
    }
    var selector = '[data-daisie-file-attachments], [data-daisie-file-image]';
    if (scope.matches && scope.matches(selector)) {
      init(scope);
    }
    scope.querySelectorAll(selector).forEach(init);
  }

  function ready() {
    scan(document);
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            scan(node);
          }
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ready);
  } else {
    ready();
  }
})();
