// Selector de tema en la cabecera del admin. Guarda en nt-theme, igual que el frontal
(function () {
  var KEY = 'nt-theme';
  var THEMES = [
    ['lava-light', 'Lava · claro'], ['lava-dark', 'Lava · oscuro'],
    ['citrus-light', 'Cítrico · claro'], ['citrus-dark', 'Cítrico · oscuro'],
    ['bloom-light', 'Bloom · claro'], ['bloom-dark', 'Bloom · oscuro'],
  ];

  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    document.documentElement.setAttribute('data-bs-theme', theme.split('-')[1]);
    try { localStorage.setItem(KEY, theme); } catch (e) {}
  }

  var nav = document.querySelector('#jazzy-navbar .navbar-nav.ms-auto');
  if (!nav) return;

  var select = document.createElement('select');
  select.className = 'form-select form-select-sm';
  select.id = 'pt-admin-theme';
  select.setAttribute('aria-label', 'Tema');
  THEMES.forEach(function (t) {
    var option = document.createElement('option');
    option.value = t[0];
    option.textContent = t[1];
    select.appendChild(option);
  });
  select.value = document.documentElement.dataset.theme;
  select.addEventListener('change', function () { apply(select.value); });

  var item = document.createElement('li');
  item.className = 'nav-item pt-admin-theme';
  item.appendChild(select);
  nav.insertBefore(item, nav.firstChild);

  // Otra pestaña (el frontal o el admin) cambió el tema
  window.addEventListener('storage', function (e) {
    if (e.key === KEY && e.newValue) { apply(e.newValue); select.value = e.newValue; }
  });
})();
