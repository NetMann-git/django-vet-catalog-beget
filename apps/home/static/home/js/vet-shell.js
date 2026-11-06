/* шаг 2: native details работает без JavaScript. */
(function () {
  'use strict';
  var header = document.querySelector('[data-vet-header]');
  var menu = document.querySelector('[data-vet-menu]');
  if (!header || !menu) return;
  var summary = menu.querySelector('summary');
  function updateHeight() {
    var height = Math.ceil(header.getBoundingClientRect().height) + 'px';
    document.documentElement.style.setProperty('--va-header-height', height);
    document.body.style.setProperty('--fm-header-height', height);
  }
  updateHeight();
  if ('ResizeObserver' in window) new ResizeObserver(updateHeight).observe(header);
  else window.addEventListener('resize', updateHeight);
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && menu.open) { menu.open = false; summary.focus(); }
  });
  document.addEventListener('click', function (event) {
    if (menu.open && !menu.contains(event.target)) menu.open = false;
  });
  menu.addEventListener('click', function (event) { if (event.target.closest('a')) menu.open = false; });
  window.addEventListener('resize', function () { menu.open = false; });
})();
