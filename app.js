const $ = id => document.getElementById(id);
let dataset = { headers: [], rows: [] };
let workbook = null;
let currentFileName = '';
let currentSheetName = '';
const demo = `日期,分组,数值,样本量
2026/7/1,A,18,24
2026/7/2,A,25,27
2026/7/3,B,16,19
2026/7/4,B,32,22
2026/7/5,C,11,15
2026/7/6,C,28,18`;

function parseDelimited(text) {
  const lines = text.trim().split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 2) throw new Error('至少需要标题行和一行数据。');
  const delimiter = lines[0].includes('\t') ? '\t' : ',';
  const split = line => line.split(delimiter).map(value => value.trim().replace(/^"|"$/g, ''));
  return matrixToDataset(lines.map(split), 0);
}
function uniqueHeaders(values) {
  const used = new Map();
  return values.map((value, index) => {
    const base = String(value ?? '').trim() || `字段${index + 1}`;
    const count = (used.get(base) || 0) + 1;
    used.set(base, count);
    return count === 1 ? base : `${base}_${count}`;
  });
}
function detectHeaderRow(matrix) {
  let bestIndex = 0, bestScore = -1;
  matrix.slice(0, 10).forEach((row, index) => {
    const filled = row.filter(value => String(value ?? '').trim() !== '').length;
    const textValues = row.filter(value => String(value ?? '').trim() !== '' && !Number.isFinite(Number(value))).length;
    const score = filled * 3 + textValues;
    if (score > bestScore) { bestScore = score; bestIndex = index; }
  });
  return bestIndex;
}
function matrixToDataset(matrix, headerIndex = detectHeaderRow(matrix)) {
  if (!matrix.length) throw new Error('这个工作表没有可读取的数据。');
  const width = Math.max(...matrix.map(row => row.length));
  const headers = uniqueHeaders(Array.from({ length: width }, (_, index) => matrix[headerIndex]?.[index] ?? ''));
  const rows = matrix.slice(headerIndex + 1)
    .filter(row => row.some(value => String(value ?? '').trim() !== ''))
    .map(row => Object.fromEntries(headers.map((header, index) => [header, String(row[index] ?? '').trim()])));
  if (!rows.length) throw new Error('已识别字段标题，但标题下方没有数据。');
  return { headers, rows, headerIndex };
}
function numericFields() {
  return dataset.headers.filter(header => {
    const values = dataset.rows.map(row => row[header]).filter(value => value !== '');
    return values.length && values.filter(value => Number.isFinite(Number(String(value).replace(/,/g, '')))).length / values.length > 0.8;
  });
}
function setDataset(nextDataset, sourceMessage) {
  dataset = nextDataset; render();
  $('message').textContent = sourceMessage; $('message').style.color = '#268460';
}
function analyzePasted() {
  try {
    workbook = null; currentSheetName = ''; $('sheetBar').classList.add('hidden'); $('historyDashboard').classList.add('hidden');
    setDataset(parseDelimited($('pasteInput').value), '分析完成，粘贴的数据只保留在当前浏览器页面中。');
  } catch (error) { showError(error); }
}
function loadWorkbookSheet(sheetName) {
  try {
    currentSheetName = sheetName;
    const matrix = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1, defval: '', raw: false });
    const nextDataset = matrixToDataset(matrix);
    $('sheetInfo').textContent = `识别第 ${nextDataset.headerIndex + 1} 行为标题`;
    setDataset(nextDataset, `已读取：${currentFileName} / ${sheetName}，共 ${nextDataset.rows.length} 条记录。`);
    renderHistoryDashboard();
  } catch (error) { showError(error); }
}
async function loadFile(file) {
  if (!file) return;
  currentFileName = file.name;
  $('message').textContent = `正在读取：${file.name}`; $('message').style.color = '#737985';
  try {
    if (/\.csv$/i.test(file.name)) {
      workbook = null; $('sheetBar').classList.add('hidden');
      const text = await file.text(); $('pasteInput').value = text;
      setDataset(parseDelimited(text), `已读取：${file.name}`); return;
    }
    if (typeof XLSX === 'undefined') throw new Error('Excel 解析组件未加载，请重新打开网页。');
    workbook = XLSX.read(await file.arrayBuffer(), { type: 'array', cellDates: true });
    $('sheetSelect').innerHTML = workbook.SheetNames.map(name => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join('');
    $('sheetBar').classList.remove('hidden');
    const preferredSheet = workbook.SheetNames.includes('2026年收益表') ? '2026年收益表' : workbook.SheetNames[0];
    $('sheetSelect').value = preferredSheet;
    loadWorkbookSheet(preferredSheet);
  } catch (error) { showError(error); }
}
function showError(error) {
  $('message').textContent = error.message || '读取失败，请检查文件格式。'; $('message').style.color = '#b42318';
}
function render() {
  const nums = numericFields();
  const cells = dataset.rows.length * dataset.headers.length;
  const filled = dataset.rows.reduce((count, row) => count + dataset.headers.filter(header => row[header] !== '').length, 0);
  $('rowCount').textContent = dataset.rows.length; $('columnCount').textContent = dataset.headers.length;
  $('numericCount').textContent = nums.length; $('completeRate').textContent = cells ? `${Math.round(filled / cells * 100)}%` : '0%';
  $('numericField').innerHTML = nums.length ? nums.map(header => `<option value="${escapeHtml(header)}">${escapeHtml(header)}</option>`).join('') : '<option value="">无数值字段</option>';
  renderSummary(nums[0]); renderTable(); drawChart(nums[0]);
  $('results').classList.remove('hidden'); $('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function stats(field) {
  const values = dataset.rows.map(row => Number(String(row[field]).replace(/,/g, ''))).filter(Number.isFinite).sort((a, b) => a - b);
  if (!values.length) return null;
  const sum = values.reduce((a, b) => a + b, 0);
  return { count: values.length, min: values[0], max: values[values.length - 1], avg: sum / values.length, median: values.length % 2 ? values[(values.length - 1) / 2] : (values[values.length / 2 - 1] + values[values.length / 2]) / 2 };
}
function renderSummary(field) {
  if (!field) { $('summary').innerHTML = '<p class="message">没有识别到数值字段。</p>'; return; }
  const summary = stats(field);
  const items = [['当前字段', field], ['有效数值', summary.count], ['最小值', fmt(summary.min)], ['最大值', fmt(summary.max)], ['平均值', fmt(summary.avg)], ['中位数', fmt(summary.median)]];
  $('summary').innerHTML = items.map(item => `<div class="summary-row"><span>${item[0]}</span><strong>${escapeHtml(String(item[1]))}</strong></div>`).join('');
}
function renderTable() {
  const rows = dataset.rows.slice(0, 100);
  $('dataTable').innerHTML = `<thead><tr>${dataset.headers.map(header => `<th>${escapeHtml(header)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${dataset.headers.map(header => `<td>${escapeHtml(row[header])}</td>`).join('')}</tr>`).join('')}</tbody>`;
}
const historyGroups = [
  {
    title: '0次组合历史累计',
    cumulative: '累计节省金额',
    columns: [['期数', '期数'], ['日期', '时间'], ['结果', '开奖号'], ['组合号码', '杀0组号码'], ['状态', '不开为中'], ['累计期数', '累计中期数'], ['单期变化', '节省金额'], ['累计变化', '累计节省金额']]
  },
  {
    title: '≥3次组合历史累计',
    cumulative: '累计盈亏',
    columns: [['期数', '期数'], ['日期', '时间'], ['结果', '开奖号'], ['组合号码', '100元档号码'], ['投入值', '投资'], ['命中值', '命中投注'], ['返回值', '返奖'], ['单期变化', '单期盈亏'], ['累计变化', '累计盈亏']]
  },
  {
    title: '≥4次组合历史累计',
    cumulative: '累计盈亏_2',
    columns: [['期数', '期数'], ['日期', '时间'], ['结果', '开奖号'], ['组合号码', '100元档号码_2'], ['投入值', '投资_2'], ['命中值', '命中投注_2'], ['返回值', '返奖_2'], ['单期变化', '单期盈亏_2'], ['累计变化', '累计盈亏_2']]
  },
  {
    title: '≥5次组合历史累计',
    cumulative: '累计盈亏_3',
    columns: [['期数', '期数'], ['日期', '时间'], ['结果', '开奖号'], ['组合号码', '100元档号码_3'], ['投入值', '投资_3'], ['命中值', '命中投注_3'], ['返回值', '返奖_3'], ['单期变化', '单期盈亏_3'], ['累计变化', '累计盈亏_3']]
  }
];
function completedHistoryRows() {
  return dataset.rows.filter(row => {
    const period = String(row['期数'] ?? '').trim();
    const result = String(row['开奖号'] ?? '').trim();
    return /^\d+期$/.test(period) && /^\d+$/.test(result);
  });
}
function renderHistoryDashboard() {
  const available = currentSheetName === '2026年收益表' && dataset.headers.includes('累计盈亏_3');
  $('historyDashboard').classList.toggle('hidden', !available);
  $('results').classList.toggle('history-only', available);
  if (!available) return;
  const rows = completedHistoryRows().slice(0, 100);
  $('historyStories').innerHTML = historyGroups.map((group, index) => {
    const latest = rows.length ? (rows[0][group.cumulative] || '—') : '—';
    const records = rows.map(row => {
      const numberColumn = group.columns[3];
      const detailColumns = group.columns.slice(4);
      return `<div class="history-record">
        <div class="record-head">
          <strong>${escapeHtml(row['期数'] || '—')}</strong>
          <span>${escapeHtml(row['时间'] || '—')}</span>
          <b>结果 ${escapeHtml(row['开奖号'] || '—')}</b>
        </div>
        <div class="record-numbers"><span>${escapeHtml(numberColumn[0])}</span><p>${escapeHtml(row[numberColumn[1]] || '—')}</p></div>
        <div class="record-metrics">${detailColumns.map(column => `<div><span>${escapeHtml(column[0])}</span><strong>${escapeHtml(row[column[1]] || '—')}</strong></div>`).join('')}</div>
      </div>`;
    }).join('');
    return `<article class="story-section">
      <div class="story-number">${String(index + 1).padStart(2, '0')}</div>
      <div class="story-title"><p>项目 ${index + 1}</p><h3>${group.title}</h3></div>
      <div class="history-summary">
        <div><span>已完成历史</span><strong>${rows.length}期</strong></div>
        <div><span>最新累计值</span><strong>${escapeHtml(latest)}</strong></div>
        <div><span>最新历史期数</span><strong>${escapeHtml(rows[0]?.['期数'] || '—')}</strong></div>
      </div>
      <div class="history-scroll">${records}</div>
    </article>`;
  }).join('');
}
function drawChart(field) {
  const canvas = $('chart'), context = canvas.getContext('2d'); context.clearRect(0, 0, canvas.width, canvas.height);
  if (!field) return;
  const values = dataset.rows.map(row => Number(String(row[field]).replace(/,/g, ''))).filter(Number.isFinite);
  if (!values.length) return;
  const bins = 8, min = Math.min(...values), max = Math.max(...values), span = max - min || 1, counts = Array(bins).fill(0);
  values.forEach(value => counts[Math.min(bins - 1, Math.floor((value - min) / span * bins))]++);
  const pad = 45, width = (canvas.width - pad * 2) / bins, peak = Math.max(...counts, 1);
  context.strokeStyle = '#ded8ca'; context.beginPath(); context.moveTo(pad, 20); context.lineTo(pad, canvas.height - 40); context.lineTo(canvas.width - 20, canvas.height - 40); context.stroke();
  counts.forEach((count, index) => {
    const height = count / peak * (canvas.height - 90), x = pad + index * width + 6, y = canvas.height - 40 - height;
    context.fillStyle = index % 2 ? '#d7332a' : '#a8171d'; context.fillRect(x, y, width - 12, height);
    context.fillStyle = '#655f56'; context.font = '13px sans-serif'; context.textAlign = 'center'; context.fillText(count, x + (width - 12) / 2, y - 8);
  });
  context.textAlign = 'left'; context.fillText(fmt(min), pad, canvas.height - 16); context.textAlign = 'right'; context.fillText(fmt(max), canvas.width - 20, canvas.height - 16);
}
function exportReport() {
  const nums = numericFields();
  let text = `奥数数据分析中心 - 通用统计报告\n生成时间：${new Date().toLocaleString()}\n数据来源：${currentFileName || '粘贴内容'}\n记录数：${dataset.rows.length}\n字段数：${dataset.headers.length}\n\n`;
  nums.forEach(field => { const summary = stats(field); text += `[${field}] 有效数值 ${summary.count}，最小值 ${fmt(summary.min)}，最大值 ${fmt(summary.max)}，平均值 ${fmt(summary.avg)}，中位数 ${fmt(summary.median)}\n`; });
  text += '\n本报告仅用于通用数学与数据统计。';
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' }), link = document.createElement('a');
  link.href = URL.createObjectURL(blob); link.download = '数据分析报告.txt'; link.click(); URL.revokeObjectURL(link.href);
}
function fmt(value) { return Number.isInteger(value) ? String(value) : value.toFixed(2); }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char])); }

$('loadDemo').onclick = () => { $('pasteInput').value = demo; analyzePasted(); };
$('analyze').onclick = analyzePasted;
$('numericField').onchange = event => { renderSummary(event.target.value); drawChart(event.target.value); };
$('exportReport').onclick = exportReport;
$('fileInput').onchange = event => loadFile(event.target.files[0]);
$('sheetSelect').onchange = event => loadWorkbookSheet(event.target.value);
