// ===== DYNAMIC OPTION ROWS (create page) =====
const container = document.getElementById('optionsContainer');
const addBtn    = document.getElementById('addOption');
const MAX_OPTS  = 8;

function updateOptionNums() {
  const rows = container ? container.querySelectorAll('.option-row') : [];
  rows.forEach((row, i) => {
    row.querySelector('.option-num').textContent = String(i + 1).padStart(2, '0');
    const inp = row.querySelector('input');
    inp.placeholder = `Option ${i + 1}`;
    inp.required = i < 2;
    const removeBtn = row.querySelector('.remove-opt');
    removeBtn.disabled = rows.length <= 2;
  });
  if (addBtn) addBtn.style.display = rows.length >= MAX_OPTS ? 'none' : '';
}

if (addBtn) {
  addBtn.addEventListener('click', () => {
    const rows = container.querySelectorAll('.option-row');
    if (rows.length >= MAX_OPTS) return;

    const div = document.createElement('div');
    div.className = 'option-row';
    div.innerHTML = `
      <span class="option-num"></span>
      <input type="text" name="option" maxlength="120">
      <button type="button" class="remove-opt" title="Remove">✕</button>
    `;
    container.appendChild(div);
    div.querySelector('input').focus();

    div.querySelector('.remove-opt').addEventListener('click', () => {
      div.remove();
      updateOptionNums();
    });

    updateOptionNums();
  });

  // Hook existing remove buttons
  container.querySelectorAll('.remove-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.option-row').remove();
      updateOptionNums();
    });
  });
}

// ===== VOTE BUTTON ENABLE =====
const voteForm = document.getElementById('voteForm');
const voteBtn  = document.getElementById('voteBtn');

if (voteBtn && voteForm) {
  voteForm.querySelectorAll('input[type="radio"]').forEach(r => {
    r.addEventListener('change', () => {
      voteBtn.disabled = false;
      voteBtn.textContent = 'Cast Your Vote →';
    });
  });
}

// ===== ANIMATE RESULT BARS =====
function animateBars() {
  document.querySelectorAll('.result-bar[data-width]').forEach((bar, i) => {
    const target = parseFloat(bar.dataset.width);
    setTimeout(() => {
      bar.style.width = target + '%';
    }, 100 + i * 80);
  });
}

if (document.querySelector('.result-bar')) {
  // Wait for paint then animate
  requestAnimationFrame(() => setTimeout(animateBars, 50));
}

// ===== COPY POLL URL =====
const copyBtn  = document.getElementById('copyBtn');
const shareUrl = document.getElementById('shareUrl');

if (copyBtn && shareUrl) {
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(shareUrl.value);
    } catch {
      shareUrl.select();
      document.execCommand('copy');
    }
    copyBtn.textContent = 'Copied!';
    copyBtn.classList.add('copied');
    setTimeout(() => {
      copyBtn.textContent = 'Copy';
      copyBtn.classList.remove('copied');
    }, 2000);
  });
}

// ===== AUTO DISMISS FLASH =====
document.querySelectorAll('.flash').forEach(f => {
  setTimeout(() => {
    f.style.transition = 'opacity 0.4s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  }, 4000);
});
