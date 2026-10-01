<script setup>
import { computed, ref, watch } from 'vue';
import { buildComparison, comparisonLineSegments, metadataRows, preferenceMatches, recordedIntensity } from '../coffeeComparison.js';

const props = defineProps({
  coffees: { type: Array, required: true },
  tags: { type: Array, required: true },
  categories: { type: Array, default: () => [] },
  profiles: { type: Object, required: true },
  preferenceId: { type: String, required: true },
  countryLabel: { type: Function, required: true },
  selectedFlavor: { type: String, default: '' }
});
const emit = defineEmits(['remove', 'clear', 'detail', 'flavor', 'coffeeFocus', 'update:preferenceId']);
const mode = ref('families');
const differencesOnly = ref(false);
const sortByGap = ref(false);
const focusedId = ref(null);
watch(() => props.coffees.map(coffee => coffee.id), ids => {
  if (!ids.includes(focusedId.value)) focusedId.value = null;
});
const modes = [{ id: 'families', label: '风味全貌' }, { id: 'intensity', label: '逐项强度' }, { id: 'lines', label: '曲线对比' }];
const colors = ['#34755e', '#b85440', '#7660a0', '#926b0e'];
const comparison = computed(() => buildComparison(props.coffees, props.tags, props.categories));
const flavorRows = computed(() => sortByGap.value
  ? [...comparison.value.rows].sort((a, b) => (b.gap ?? -1) - (a.gap ?? -1) || b.peak - a.peak)
  : comparison.value.rows);
const metadata = computed(() => metadataRows(props.coffees, props.countryLabel).filter(row => !differencesOnly.value || row.different));
const profile = computed(() => props.profiles[props.preferenceId]);
const matches = computed(() => props.coffees.map(coffee => preferenceMatches(coffee, profile.value.tags)));
const tagNames = computed(() => Object.fromEntries(props.tags.map(tag => [tag.id, tag.name])));
const gapDetails = computed(() => {
  const row = comparison.value.biggestGap;
  if (!row) return null;
  const entries = row.values.map((value, index) => ({ value, name: props.coffees[index].name })).filter(entry => entry.value !== null);
  const strongest = entries.reduce((a, b) => a.value >= b.value ? a : b);
  const mildest = entries.reduce((a, b) => a.value <= b.value ? a : b);
  return { ...row, strongest, mildest };
});
const chartWidth = computed(() => Math.max(760, comparison.value.rows.length * 76 + 110));
const x = index => comparison.value.rows.length < 2 ? chartWidth.value / 2 : 70 + index * (chartWidth.value - 105) / (comparison.value.rows.length - 1);
const y = value => 34 + (5 - value) * 51;
function linePath(index, missing) {
  return comparisonLineSegments(comparison.value.rows.map(row => row.values[index]))
    .filter(segment => segment.missing === missing)
    .map(({ from, to }) => `M${x(from.index)},${y(from.value)} L${x(to.index)},${y(to.value)}`).join(' ');
}
function heatStyle(value) {
  if (value === null) return {};
  return { background: ['#edf2ed', '#d5e5da', '#aecbb9', '#6b9b83', '#2f6f59'][value - 1] || '#6b9b83', color: value === 5 ? '#fff' : '#202d27' };
}
function focus(index) {
  return (focusedId.value && focusedId.value !== props.coffees[index].id) ||
    (props.selectedFlavor && recordedIntensity(props.coffees[index], props.selectedFlavor) === null);
}
</script>

<template>
  <section class="bean-comparison" :style="{ '--bean-count': coffees.length }" aria-labelledby="comparison-title">
    <div class="comparison-heading">
      <div><p class="kicker">COMPARE / {{ coffees.length }} 款已选豆子</p><h2 id="comparison-title">样本风味对比</h2></div>
      <button class="text-button" type="button" @click="emit('clear')">清空对比</button>
    </div>

    <div class="comparison-selected" aria-label="已选样本与颜色">
      <div v-for="(coffee, index) in coffees" :key="coffee.id" class="comparison-selected-item" :style="{ '--series-color': colors[index] }" @mouseenter="focusedId = coffee.id; emit('coffeeFocus', coffee.id)" @mouseleave="focusedId = null; emit('coffeeFocus', null)" @focusin="focusedId = coffee.id; emit('coffeeFocus', coffee.id)" @focusout="focusedId = null; emit('coffeeFocus', null)">
        <i aria-hidden="true"></i><span>{{ coffee.name }}</span>
        <button type="button" class="comparison-remove" :aria-label="`移除${coffee.name}`" :title="`移除${coffee.name}`" @click="emit('remove', coffee)">×</button>
      </div>
    </div>

    <div v-if="selectedFlavor" class="comparison-filter-context" aria-live="polite">
      <strong>{{ tagNames[selectedFlavor] || selectedFlavor }}</strong>
      <span v-for="(coffee, index) in coffees" :key="coffee.id" :style="{ '--series-color': colors[index] }"><i></i>{{ coffee.name }} <b>{{ recordedIntensity(coffee, selectedFlavor) === null ? '未记录' : `${recordedIntensity(coffee, selectedFlavor)} / 5` }}</b></span>
    </div>

    <div v-if="coffees.length > 1" class="comparison-insights" aria-live="polite">
      <div><span class="comparison-eyebrow">共同风味</span><h3>{{ comparison.shared.length ? comparison.shared.map(row => row.name).join('、') : '没有共同记录的标签' }}</h3><p>{{ comparison.shared.length ? '以上风味在每款已选样本中都有记录。' : '可以从不同的风味方向开始尝试。' }}</p></div>
      <div><span class="comparison-eyebrow">最明显的强度差异</span><template v-if="gapDetails"><h3>{{ gapDetails.name }} <small>相差 {{ gapDetails.gap }} 级</small></h3><p>{{ gapDetails.strongest.name }} {{ gapDetails.strongest.value }}/5 · {{ gapDetails.mildest.name }} {{ gapDetails.mildest.value }}/5</p></template><template v-else><h3>暂无可量化的强度差异</h3><p>共同记录的标签强度相同，或缺少可比较的记录。</p></template></div>
    </div>
    <p v-else class="comparison-single">再选择一款豆子，即可查看共同风味和强度差异。</p>

    <div class="comparison-controls">
      <div class="comparison-modes" role="group" aria-label="图表视图"><button v-for="item in modes" :key="item.id" type="button" :aria-pressed="mode === item.id" :class="{ active: mode === item.id }" @click="mode = item.id">{{ item.label }}</button></div>
      <label class="comparison-preference">我的口味<select :value="preferenceId" @change="emit('update:preferenceId', $event.target.value)"><option v-for="(item, id) in profiles" :key="id" :value="id">{{ item.title }}</option></select></label>
    </div>

    <div class="comparison-table-scroll" tabindex="0" aria-label="咖啡风味对比数据">
      <table class="comparison-table">
        <caption class="sr-only">已选咖啡的口味匹配和风味强度</caption>
        <thead><tr><th scope="col">对比维度</th><th v-for="(coffee, index) in coffees" :key="coffee.id" scope="col" :class="{ 'comparison-dimmed': focus(index) }"><span class="comparison-column-index" :style="{ color: colors[index] }">0{{ index + 1 }} / {{ countryLabel(coffee.country) }}</span><b>{{ coffee.name }}</b><button type="button" class="comparison-detail" @click="emit('detail', coffee)">查看详情与评价 →</button></th></tr></thead>
        <tbody>
          <tr class="comparison-match-row"><th scope="row">{{ profile.title }}<small>目标口味匹配</small></th><td v-for="(coffee, index) in coffees" :key="coffee.id" :class="{ 'comparison-dimmed': focus(index) }"><strong>{{ matches[index].length }} / {{ profile.tags.length }}</strong><span>{{ matches[index].map(match => tagNames[match.id] || match.id).join(' · ') || '未记录对应风味' }}</span></td></tr>
          <tr class="comparison-signature-row"><th scope="row">风味重点<small>强度最高的三个标签</small></th><td v-for="(signature, index) in comparison.signatures" :key="signature.coffee.id" :class="{ 'comparison-dimmed': focus(index) }"><span v-for="row in signature.top" :key="row.id">{{ row.name }} <b>{{ row.values[index] }}/5</b></span><span v-if="!signature.top.length" class="comparison-missing">—</span><small v-if="signature.unique.length">仅该款有记录：{{ signature.unique.map(row => row.name).join('、') }}</small></td></tr>
        </tbody>
        <tbody v-if="mode === 'families'">
          <tr v-for="family in comparison.families" :key="family.name"><th scope="row">{{ family.name }}</th><td v-for="(cell, index) in family.cells" :key="coffees[index].id" :class="{ 'comparison-dimmed': focus(index) }"><div v-if="cell.value !== null" class="family-strength"><div class="family-meter"><i :key="`${coffees[index].id}-${cell.value}`" :style="{ transform: `scaleX(${cell.value / 5})`, background: colors[index] }"></i></div><b>{{ cell.value }}<small>/5</small></b></div><span v-else class="comparison-missing">—</span><small class="family-tag">{{ cell.tags.join(' · ') }}</small></td></tr>
          <tr v-if="!comparison.families.length"><td :colspan="coffees.length + 1" class="comparison-empty">这些样本暂无风味强度记录。</td></tr>
        </tbody>
        <tbody v-else-if="mode === 'intensity'">
          <tr v-for="row in flavorRows" :key="row.id" :class="{ 'comparison-flavor-selected': selectedFlavor === row.id }"><th scope="row"><button type="button" class="comparison-flavor-filter" :aria-pressed="selectedFlavor === row.id" :title="`筛选${row.name}风味的样本`" @click="emit('flavor', row.id)">{{ row.name }} <span aria-hidden="true">↗</span></button><small>{{ row.category }}</small></th><td v-for="(value, index) in row.values" :key="coffees[index].id" :class="{ 'comparison-dimmed': focus(index) }"><span class="intensity-cell" :class="{ missing: value === null }" :style="heatStyle(value)">{{ value ?? '—' }}<small v-if="value !== null">/5</small></span></td></tr>
          <tr v-if="!flavorRows.length"><td :colspan="coffees.length + 1" class="comparison-empty">这些样本暂无风味强度记录。</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="mode === 'lines'" class="comparison-chart-scroll" tabindex="0" aria-label="风味强度曲线">
      <svg class="comparison-line-chart" :viewBox="`0 0 ${chartWidth} 300`" :style="{ minWidth: `${chartWidth}px` }" role="group" aria-label="已选咖啡的风味强度曲线，虚线跨过未记录的标签">
        <template v-for="(row, index) in comparison.rows" :key="row.id"><rect v-if="selectedFlavor === row.id" :x="x(index) - 24" y="25" width="48" height="266" fill="#dce9df" rx="4" /></template>
        <g v-for="level in [5, 4, 3, 2, 1]" :key="level" class="comparison-grid-line"><line x1="70" :y1="y(level)" :x2="chartWidth - 35" :y2="y(level)" /><text x="47" :y="y(level) + 4" text-anchor="end">{{ level }}</text></g>
        <g v-for="(row, index) in comparison.rows" :key="row.id" class="comparison-chart-axis" role="button" tabindex="0" :aria-label="`筛选${row.name}风味`" :aria-pressed="selectedFlavor === row.id" @click="emit('flavor', row.id)" @keydown.enter="emit('flavor', row.id)" @keydown.space.prevent="emit('flavor', row.id)"><line :x1="x(index)" y1="34" :x2="x(index)" :y2="y(1)" /><text :x="x(index)" y="276" text-anchor="middle">{{ row.name }}</text><rect :x="x(index) - 30" y="254" width="60" height="42" fill="transparent" /></g>
        <g v-for="(coffee, index) in coffees" :key="coffee.id" class="comparison-series" :class="{ 'comparison-dimmed': focus(index) }" @mouseenter="focusedId = coffee.id; emit('coffeeFocus', coffee.id)" @mouseleave="focusedId = null; emit('coffeeFocus', null)"><path :d="linePath(index, false)" :stroke="colors[index]" /><path class="comparison-missing-bridge" :d="linePath(index, true)" :stroke="colors[index]" stroke-dasharray="5 5" /><template v-for="(row, tagIndex) in comparison.rows" :key="row.id"><circle v-if="row.values[index] !== null" :cx="x(tagIndex)" :cy="y(row.values[index])" :r="selectedFlavor === row.id ? 7 : 5" :fill="colors[index]" @click="emit('flavor', row.id)"><title>{{ coffee.name }} · {{ row.name }}：{{ row.values[index] }} / 5</title></circle></template></g>
      </svg>
      <p v-if="!comparison.rows.length" class="comparison-empty">这些样本暂无风味强度记录。</p>
    </div>
    <div class="comparison-chart-notes"><p>{{ mode === 'families' ? '大类强度取该类已记录标签的最高值。' : '风味强度采用样本记录的 1–5 级。' }} “—”为未记录，不代表没有该风味。<template v-if="mode === 'lines'">虚线仅连接两端记录，跨过的风味没有测量值。</template></p><label v-if="mode === 'intensity'" class="comparison-checkbox"><input v-model="sortByGap" type="checkbox" />强度差异优先</label></div>

    <div class="comparison-meta-heading"><h3>产地与工艺对照</h3><label class="comparison-checkbox"><input v-model="differencesOnly" type="checkbox" />只看不同项</label></div>
    <div class="comparison-table-scroll" tabindex="0" aria-label="产地与工艺信息">
      <table class="comparison-table comparison-metadata"><caption class="sr-only">产地、品种、工艺和样本来源</caption><thead><tr><th scope="col">样本信息</th><th v-for="(coffee, index) in coffees" :key="coffee.id" scope="col"><span :style="{ color: colors[index] }">0{{ index + 1 }}</span> {{ coffee.name }}</th></tr></thead><tbody><tr v-for="row in metadata" :key="row.key"><th scope="row">{{ row.label }}<i v-if="row.different" class="metadata-difference" title="这些样本的信息不同" aria-label="有差异"></i></th><td v-for="(value, index) in row.values" :key="coffees[index].id">{{ value ?? '—' }}</td></tr><tr v-if="!metadata.length"><td :colspan="coffees.length + 1" class="comparison-empty">当前样本的已录入信息相同。</td></tr></tbody></table>
    </div>
    <p class="comparison-source-note">对比依据为样本资料及已录入风味，不是个人口味的保证；产地、处理法与烘焙度不能单独决定杯中表现。</p>
  </section>
</template>

<style scoped>
.bean-comparison { margin-top: 36px; padding: 30px 0 0; border-top: 2px solid var(--green); --comparison-muted: #53645a; }
.comparison-heading, .comparison-controls, .comparison-meta-heading, .comparison-chart-notes { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.comparison-heading h2 { margin: 0; font-size: 28px; line-height: 1.35; letter-spacing: 0; }
#comparison-title { scroll-margin-top: 110px; }
.comparison-heading .kicker { margin-bottom: 8px; }
.comparison-heading .text-button { min-height: 44px; flex-shrink: 0; }
.comparison-selected { display: flex; flex-wrap: wrap; gap: 12px 22px; margin: 24px 0; }
.comparison-selected-item { display: grid; grid-template-columns: 10px minmax(0, 1fr) 32px; align-items: center; gap: 9px; max-width: 100%; border-bottom: 2px solid var(--series-color); font-size: 13px; }
.comparison-selected-item > i { width: 10px; height: 10px; border-radius: 50%; background: var(--series-color); }
.comparison-selected-item > span { overflow-wrap: anywhere; }
.comparison-filter-context { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 22px; margin: 18px 0; padding: 16px; background: #eaf0e9; font-size: 13px; }
.comparison-filter-context > strong { color: var(--green); }
.comparison-filter-context > span { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 7px; }
.comparison-filter-context i { width: 8px; height: 8px; background: var(--series-color); border-radius: 50%; }
.comparison-filter-context b { font-size: 12px; }
.comparison-remove { min-height: 44px; width: 32px; font-size: 22px; background: transparent; color: var(--comparison-muted); }
.comparison-remove:hover { color: #a33d36; }
.comparison-insights { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; padding: 24px 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.comparison-eyebrow { color: var(--comparison-muted); font-size: 12px; }
.comparison-insights h3 { margin: 7px 0; font-size: 20px; font-weight: 700; line-height: 1.5; }
.comparison-insights h3 small { margin-left: 8px; color: var(--green); font-size: 13px; }
.comparison-insights p, .comparison-single { margin: 0; color: var(--comparison-muted); font-size: 13px; overflow-wrap: anywhere; }
.comparison-single { padding: 12px 0; }
.comparison-controls { margin: 26px 0 18px; flex-wrap: wrap; }
.comparison-modes { display: flex; border-bottom: 1px solid var(--line); }
.comparison-modes button { min-height: 44px; padding: 10px 17px; background: transparent; color: var(--comparison-muted); border-bottom: 2px solid transparent; font-size: 14px; }
.comparison-modes button.active { border-color: var(--green); color: var(--green); font-weight: 800; }
.comparison-preference { display: flex; align-items: center; gap: 10px; color: var(--comparison-muted); font-size: 13px; }
.comparison-preference select { min-height: 44px; padding: 7px 32px 7px 12px; background: var(--paper); color: var(--ink); border: 1px solid var(--line); }
.comparison-table-scroll, .comparison-chart-scroll { width: 100%; overflow-x: auto; overscroll-behavior-x: contain; }
.comparison-table { width: 100%; min-width: calc(140px + var(--bean-count) * 200px); table-layout: fixed; border-collapse: collapse; font-size: 14px; }
.comparison-table th, .comparison-table td { border-bottom: 1px solid var(--line); padding: 16px 20px; text-align: left; vertical-align: middle; overflow-wrap: anywhere; }
.comparison-table tr > :first-child { width: 140px; }
.comparison-table thead th { background: #e9efea; vertical-align: top; }
.comparison-table thead b { display: block; min-height: 46px; margin-top: 7px; line-height: 1.5; }
.comparison-column-index { font: 700 11px/1.5 var(--mono); }
.comparison-detail { min-height: 44px; margin-top: 6px; padding: 0; background: transparent; color: var(--green); text-align: left; font-size: 12px; }
.comparison-detail:hover { text-decoration: underline; }
.comparison-table tbody th { font-weight: 600; }
.comparison-table th > small { display: block; margin-top: 4px; color: var(--comparison-muted); font-size: 11px; font-weight: 400; }
.comparison-match-row td { background: #f2f5f1; }
.comparison-match-row strong { font-size: 22px; color: var(--green); font-family: var(--display); }
.comparison-match-row td > span { display: block; margin-top: 2px; font-size: 12px; color: var(--comparison-muted); }
.comparison-signature-row td > span { display: block; font-size: 13px; line-height: 1.8; }
.comparison-signature-row td b { margin-left: 5px; color: var(--comparison-muted); font: 600 11px var(--mono); }
.comparison-signature-row td > small { display: block; margin-top: 6px; color: var(--comparison-muted); font-size: 11px; }
.family-strength { display: grid; grid-template-columns: minmax(0, 1fr) 35px; align-items: center; gap: 10px; }
.family-meter { height: 8px; background: #e3e7e1; overflow: hidden; border-radius: 2px; }
.family-meter i { display: block; height: 100%; width: 100%; transform-origin: left; animation: meter-in .4s ease-out; }
.family-strength b { font: 700 15px var(--mono); text-align: right; }
.family-strength b small { margin-left: 2px; color: var(--comparison-muted); font-size: 10px; }
.family-tag { display: block; margin-top: 5px; min-height: 18px; color: var(--comparison-muted); font-size: 12px; }
.comparison-missing { color: var(--comparison-muted); }
.comparison-flavor-filter { min-height: 44px; padding: 0; background: transparent; text-align: left; color: var(--ink); font-weight: 700; }
.comparison-flavor-filter > span { color: var(--green); margin-left: 6px; }
.comparison-flavor-filter:hover { color: var(--green); }
.comparison-flavor-selected { background: #eaf0e9; }
.intensity-cell { min-height: 38px; display: flex; align-items: center; justify-content: center; gap: 3px; border-radius: 3px; font: 700 16px var(--mono); }
.intensity-cell > small { font-size: 10px; opacity: .9; }
.intensity-cell.missing { color: var(--comparison-muted); background: #f0f1ed; }
.comparison-table tbody tr:hover { background: #eef3ed; }
.comparison-chart-notes { margin-top: 12px; align-items: flex-start; }
.comparison-chart-notes > p, .comparison-source-note { margin: 0; color: var(--comparison-muted); font-size: 12px; }
.comparison-checkbox { display: inline-flex; align-items: center; gap: 6px; min-height: 32px; font-size: 13px; color: var(--comparison-muted); white-space: nowrap; }
.comparison-checkbox input { width: 16px; height: 16px; margin: 0; accent-color: var(--green); }
.comparison-meta-heading { margin: 35px 0 15px; }
.comparison-meta-heading h3 { margin: 0; font-size: 20px; }
.comparison-metadata th, .comparison-metadata td { padding-top: 13px; padding-bottom: 13px; }
.comparison-metadata thead th { font-size: 13px; }
.comparison-metadata thead span { font-family: var(--mono); }
.metadata-difference { display: inline-block; width: 5px; height: 5px; margin-left: 8px; vertical-align: middle; border-radius: 50%; background: var(--coral); }
.comparison-source-note { padding-top: 18px; }
.comparison-empty { padding: 28px !important; color: var(--comparison-muted); }
.comparison-line-chart { display: block; width: 100%; margin-top: 24px; overflow: visible; }
.comparison-grid-line line { stroke: #cad4cc; stroke-width: 1; }
.comparison-grid-line text, .comparison-chart-axis text { fill: #4e6055; font-size: 12px; }
.comparison-chart-axis line { stroke: #e0e6df; }
.comparison-series { transition: opacity .2s ease; }
.comparison-series path { fill: none; stroke-width: 2.8; stroke-linejoin: round; stroke-linecap: round; }
.comparison-series circle { stroke: var(--paper); stroke-width: 1.8; }
.comparison-series .comparison-missing-bridge { opacity: .7; }
.comparison-chart-axis { cursor: pointer; }
.comparison-chart-axis:hover text, .comparison-chart-axis:focus-visible text { fill: var(--green); font-weight: 800; }
.comparison-series:hover path { stroke-width: 4; }
.comparison-dimmed { opacity: .65; transition: opacity .2s ease; }
.comparison-series.comparison-dimmed { opacity: .28; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
@keyframes meter-in { from { opacity: 0; } to { opacity: 1; } }
@media (max-width: 650px) { .comparison-heading { align-items: flex-start; }.comparison-heading h2 { font-size: 23px; }.comparison-insights { grid-template-columns: 1fr; gap: 20px; }.comparison-controls { align-items: flex-start; flex-direction: column; gap: 16px; }.comparison-modes { width: 100%; }.comparison-modes button { flex: 1; padding: 10px 8px; }.comparison-chart-notes { flex-direction: column; gap: 8px; }.comparison-table th, .comparison-table td { padding-left: 14px; padding-right: 14px; }.comparison-meta-heading { gap: 10px; }.comparison-meta-heading h3 { font-size: 18px; } }
@media (max-width: 1000px) { .comparison-table tr > :first-child { position: sticky; left: 0; z-index: 1; background: var(--paper); box-shadow: 1px 0 0 var(--line); }.comparison-table thead tr > :first-child { background: #e9efea; }.comparison-table .comparison-flavor-selected > :first-child { background: #eaf0e9; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
