(() => {
  'use strict';
  const controls = document.querySelector('.case-filters');
  if (!controls) return;
  const cards = Array.from(document.querySelectorAll('[data-case-domain]'));
  const status = document.getElementById('case-filter-status');
  controls.hidden = false;
  controls.querySelectorAll('[data-case-filter]').forEach(button => {
    button.addEventListener('click', () => {
      const filter = button.dataset.caseFilter;
      let count = 0;
      cards.forEach(card => {
        card.hidden = filter !== 'all' && card.dataset.caseDomain !== filter;
        if (!card.hidden) count += 1;
      });
      controls.querySelectorAll('[data-case-filter]').forEach(item => {
        item.setAttribute('aria-pressed', String(item === button));
      });
      status.textContent = button.textContent.replace(/\s+\d+건$/, '') + ' · 고정 사례 ' + count + '건';
    });
  });
})();
