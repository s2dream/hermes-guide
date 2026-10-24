(() => {
  'use strict';
  const toast = document.getElementById('toast');
  let timer;
  function announce(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove('show'), 3200);
  }
  async function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(value); return true; } catch (_) { /* Use fallback. */ }
    }
    const field = document.createElement('textarea');
    field.value = value;
    field.setAttribute('readonly', '');
    field.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    document.body.appendChild(field);
    field.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch (_) { /* Offer manual selection. */ }
    field.remove();
    return copied;
  }
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const code = document.getElementById(button.dataset.copy);
      const copied = await copyText(code.textContent.trim());
      button.focus({preventScroll: true});
      if (copied) {
        button.textContent = '복사됨 ✓';
        announce('복사했어요. 명령어와 예시 값을 확인한 뒤 내 터미널이나 설정 파일에 붙여넣으세요.');
        setTimeout(() => { button.textContent = '복사'; }, 2200);
      } else {
        const range = document.createRange();
        range.selectNodeContents(code);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        announce('자동 복사가 제한되어 있어요. 선택된 내용을 직접 복사하세요.');
      }
    });
  });
  if ('IntersectionObserver' in window) {
    const links = Array.from(document.querySelectorAll('.sidebar nav a'));
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        links.forEach(link => {
          if (link.hash === '#' + entry.target.id) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      });
    }, {rootMargin: '-15% 0px -65% 0px', threshold: 0});
    document.querySelectorAll('.section').forEach(section => observer.observe(section));
  }
})();
