const priceEl = document.getElementById('price');
const changeEl = document.getElementById('change');
const updatedEl = document.getElementById('updated');
const errorEl = document.getElementById('error');
const statusEl = document.getElementById('status');
const loaderEl = document.getElementById('loader');
const symbolEl = document.getElementById('symbol');

function setLoading(loading) {
  loaderEl.classList.toggle('show', loading);
}

function formatTime(iso) {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '--' : date.toLocaleString('zh-CN', { hour12: false });
}

function renderData(data) {
  symbolEl.textContent = data.symbol || 'XAU/USD';
  priceEl.textContent = `$${Number(data.price).toFixed(2)}`;
  const sign = data.change_24h >= 0 ? '+' : '';
  changeEl.textContent = `${sign}${Number(data.change_24h).toFixed(2)} (${sign}${Number(data.change_percent_24h).toFixed(2)}%)`;
  changeEl.className = `change ${data.change_24h >= 0 ? 'up' : 'down'}`;
  updatedEl.textContent = `更新时间：${formatTime(data.updated_at)}`;
  statusEl.textContent = data.cached ? '数据来源：缓存（20秒）' : '数据来源：实时';
  errorEl.textContent = '';
}

async function fetchGoldPrice() {
  setLoading(true);
  try {
    const response = await fetch('/api/gold', { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }
    renderData(data);
  } catch (err) {
    errorEl.textContent = `加载失败：${err.message}`;
    statusEl.textContent = '请稍后重试';
  } finally {
    setLoading(false);
  }
}

fetchGoldPrice();
setInterval(fetchGoldPrice, 30000);
