(() => {
  const button = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#navegacao');
  if (!button || !nav) return;
  button.hidden = false;
  document.documentElement.classList.add('has-js');
  const close = () => {
    button.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  };
  button.addEventListener('click', () => {
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    nav.classList.toggle('is-open', !expanded);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      close();
      button.focus();
    }
  });
  document.addEventListener('click', event => {
    if (!nav.contains(event.target) && !button.contains(event.target)) close();
  });
  window.matchMedia('(min-width: 900px)').addEventListener('change', close);
})();
