/* Cally calendar: show the event panel for the selected day. */
(function () {
  function show(root, date) {
    root.querySelectorAll('[data-daisie-calendar-day]').forEach(function (day) {
      day.hidden = day.getAttribute('data-daisie-calendar-day') !== date;
    });
  }

  function init(root) {
    var calendar = root.querySelector('calendar-date');
    if (!calendar) {
      return;
    }
    var initial =
      calendar.getAttribute('value') ||
      root.getAttribute('data-initial-date') ||
      '';
    show(root, initial);
    calendar.addEventListener('change', function () {
      show(root, calendar.value);
    });
  }

  function initAll() {
    document.querySelectorAll('[data-daisie-calendar]').forEach(init);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
