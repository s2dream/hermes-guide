(() => {
  'use strict';
  document.querySelectorAll('.nav-group').forEach(group => {
    const summary = group.querySelector('summary');
    group.addEventListener('keydown', event => {
      if (event.key === 'Escape' && group.open) {
        group.open = false;
        summary.focus();
        event.preventDefault();
      }
    });
    document.addEventListener('click', event => {
      if (!group.contains(event.target)) group.open = false;
    });
    document.addEventListener('focusin', event => {
      if (!group.contains(event.target)) group.open = false;
    });
  });
})();
