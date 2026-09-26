/* Feed: AJAX filtering with load-more / infinite scroll. */
(function () {
  function formParams(form) {
    var params = new URLSearchParams();
    if (!form) {
      return params;
    }
    new FormData(form).forEach(function (value, key) {
      if (value === '' || value == null) {
        return;
      }
      params.append(key, value);
    });
    return params;
  }

  function init(root) {
    var form = root.querySelector('[data-daisie-feed-form]');
    var items = root.querySelector('[data-daisie-feed-items]');
    var status = root.querySelector('[data-daisie-feed-status]');
    var more = root.querySelector('[data-daisie-feed-more]');
    var url = root.getAttribute('data-url');
    var infinite = root.getAttribute('data-infinite') === 'true';
    if (!items || !url) {
      return;
    }
    var offset = parseInt(root.getAttribute('data-offset') || '0', 10) || 0;
    var hasMore = !!more;
    var loading = false;

    var container = root.querySelector('[data-daisie-feed-items]');
    var toggle = root.querySelector('[data-daisie-feed-toggle]');
    var storageKey = 'daisie-feed-layout:' + (url || window.location.pathname);

    function applyLayout(name) {
      if (!container || !toggle) {
        return;
      }
      var script = document.getElementById('daisie-feed-layout-classes');
      var map = {};
      try {
        map = script ? JSON.parse(script.textContent) : {};
      } catch (e) {
        map = {};
      }
      if (!map[name]) {
        return;
      }
      container.className = map[name];
      toggle
        .querySelectorAll('[data-daisie-feed-layout-option]')
        .forEach(function (input) {
          var on = input.value === name;
          input.checked = on;
          var label = input.closest('label');
          if (label) {
            label.classList.toggle('btn-active', on);
          }
        });
    }

    if (toggle) {
      toggle.hidden = false;
      var saved = null;
      try {
        saved = window.localStorage.getItem(storageKey);
      } catch (e) {
        saved = null;
      }
      if (saved) {
        applyLayout(saved);
      }
      toggle.addEventListener('change', function (event) {
        if (!event.target.matches('[data-daisie-feed-layout-option]')) {
          return;
        }
        applyLayout(event.target.value);
        try {
          window.localStorage.setItem(storageKey, event.target.value);
        } catch (e) {
          /* storage unavailable */
        }
      });
    }

    function setStatus(message) {
      if (status) {
        status.textContent = message || '';
      }
    }

    function load(reset) {
      if (loading) {
        return;
      }
      loading = true;
      root.setAttribute('aria-busy', 'true');
      setStatus(reset ? 'Loading…' : 'Loading more…');

      var params = formParams(form);
      params.set('offset', String(reset ? 0 : offset));

      fetch(url + '?' + params.toString(), {
        headers: { Accept: 'application/json' },
      })
        .then(function (response) {
          return response.ok ? response.json() : null;
        })
        .then(function (data) {
          if (!data) {
            setStatus('Could not load');
            return;
          }
          if (reset) {
            items.innerHTML = '';
          }
          items.insertAdjacentHTML('beforeend', data.html);
          offset = data.next_offset;
          hasMore = data.has_more;
          if (more) {
            more.parentElement.hidden = !hasMore;
          }
          if (window.history && window.history.replaceState) {
            var clean = formParams(form).toString();
            window.history.replaceState(
              null,
              '',
              window.location.pathname + (clean ? '?' + clean : ''),
            );
          }
          setStatus(data.total + ' item' + (data.total === 1 ? '' : 's'));
        })
        .catch(function () {
          setStatus('Could not load');
        })
        .then(function () {
          loading = false;
          root.removeAttribute('aria-busy');
        });
    }

    if (form) {
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        load(true);
      });
      var timer;
      form.addEventListener('change', function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          load(true);
        }, 150);
      });
      form.addEventListener('input', function (event) {
        if (event.target && event.target.type === 'search') {
          clearTimeout(timer);
          timer = setTimeout(function () {
            load(true);
          }, 350);
        }
      });
    }

    if (more) {
      more.addEventListener('click', function (event) {
        event.preventDefault();
        if (hasMore) {
          load(false);
        }
      });
      if (infinite && 'IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting && hasMore && !loading) {
              load(false);
            }
          });
        }).observe(more);
      }
    }
  }

  function initAll() {
    document.querySelectorAll('[data-daisie-feed]').forEach(function (root) {
      if (!root.dataset.daisieFeedReady) {
        root.dataset.daisieFeedReady = '1';
        init(root);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
