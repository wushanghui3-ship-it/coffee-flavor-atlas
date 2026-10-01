<script setup>
import { computed, ref } from 'vue';
const props = defineProps({
  tags: Array, categories: Array, colors: Object, coffees: Array, matches: Array,
  selectedFlavor: String, focusCoffee: Object, compareIds: Array
});
const emit = defineEmits(['flavor', 'compare', 'toggle']);
const hoverId = ref('');
const activeTag = computed(() => props.tags.find(tag => tag.id === (hoverId.value || props.selectedFlavor)));
const activeCount = computed(() => activeTag.value
  ? props.coffees.filter(coffee => Number(coffee.flavors?.[activeTag.value.id]) > 0).length
  : props.coffees.length);
const matches = computed(() => [...props.matches].sort((a, b) =>
  Number(b.flavors?.[props.selectedFlavor] || 0) - Number(a.flavors?.[props.selectedFlavor] || 0)).slice(0, 3));
const segments = computed(() => {
  const grouped = props.categories.flatMap(category => props.tags.filter(tag => tag.category === category.name));
  const source = [...grouped, ...props.tags.filter(tag => !grouped.includes(tag))];
  return source.map((tag, index) => {
    const start = index / source.length * Math.PI * 2 - Math.PI / 2 + .013;
    const end = (index + 1) / source.length * Math.PI * 2 - Math.PI / 2 - .013;
    return { ...tag, start, end, mid: (start + end) / 2, color: props.colors[tag.category] || '#6e8775' };
  });
});
function point(radius, angle) { return { x: 260 + Math.cos(angle) * radius, y: 260 + Math.sin(angle) * radius }; }
function arc(segment) {
  const a = point(191, segment.start), b = point(191, segment.end);
  const c = point(111, segment.end), d = point(111, segment.start);
  const large = segment.end - segment.start > Math.PI ? 1 : 0;
  return `M${a.x},${a.y} A191,191 0 ${large} 1 ${b.x},${b.y} L${c.x},${c.y} A111,111 0 ${large} 0 ${d.x},${d.y}Z`;
}
function segmentStyle(segment) {
  const raised = hoverId.value === segment.id || props.selectedFlavor === segment.id;
  const distance = raised ? 9 : 0;
  return {
    '--shift-x': `${Math.cos(segment.mid) * distance}px`,
    '--shift-y': `${Math.sin(segment.mid) * distance}px`
  };
}
function hasFocusFlavor(id) { return Number(props.focusCoffee?.flavors?.[id]) > 0; }
</script>

<template>
  <div class="analysis-layout flavor-explorer">
    <div class="wheel-panel panel-line">
      <div class="subheading"><div><span class="step-label">A</span><h2>风味轮盘</h2></div><span class="selection-label">{{ selectedFlavor ? `已选：${tags.find(t => t.id === selectedFlavor)?.name}` : '全部风味' }}</span></div>
      <div class="wheel-stage">
        <svg viewBox="0 0 520 520" role="group" aria-label="咖啡风味筛选">
          <g v-for="segment in segments" :key="segment.id" class="flavor-sector"
            :class="{ active: selectedFlavor === segment.id, raised: hoverId === segment.id || selectedFlavor === segment.id, 'coffee-highlight': hasFocusFlavor(segment.id), dimmed: focusCoffee && !hasFocusFlavor(segment.id) }"
            :style="segmentStyle(segment)" role="button" tabindex="0"
            :aria-label="`筛选${segment.name}风味`" :aria-pressed="selectedFlavor === segment.id"
            @mouseenter="hoverId = segment.id" @mouseleave="hoverId = ''" @focus="hoverId = segment.id" @blur="hoverId = ''"
            @click="emit('flavor', segment.id)" @keydown.enter="emit('flavor', segment.id)" @keydown.space.prevent="emit('flavor', segment.id)">
            <path :d="arc(segment)" :fill="segment.color" class="sector-fill" />
            <path :d="arc(segment)" class="sector-outline" />
            <text :x="point(151, segment.mid).x" :y="point(151, segment.mid).y" text-anchor="middle" dominant-baseline="middle" class="sector-label">{{ segment.name }}</text>
            <title>{{ segment.name }} · {{ segment.category }}{{ hasFocusFlavor(segment.id) ? ` · ${focusCoffee.name} ${focusCoffee.flavors[segment.id]}/5` : '' }}</title>
          </g>
          <circle cx="260" cy="260" r="103" fill="#202d27" />
          <text x="260" y="231" text-anchor="middle" class="center-category">{{ activeTag?.category || 'COFFEE FLAVOR' }}</text>
          <text x="260" y="267" text-anchor="middle" class="center-name">{{ activeTag?.name || '风味图谱' }}</text>
          <text x="260" y="299" text-anchor="middle" class="center-count">{{ activeCount }} 款相关样本</text>
        </svg>
      </div>
      <p v-if="focusCoffee" class="wheel-coffee-context" aria-live="polite">对比样本 · <b>{{ focusCoffee.name }}</b></p>
    </div>
    <aside class="analysis-side">
      <div class="wheel-matches panel-line" aria-live="polite">
        <p class="kicker">{{ selectedFlavor ? tags.find(t => t.id === selectedFlavor)?.name + ' · 匹配样本' : '全部风味 · 匹配样本' }}</p>
        <div class="match-total"><strong>{{ props.matches.length }}</strong><span>款豆子</span></div>
        <p class="flavor-description">{{ tags.find(t => t.id === selectedFlavor)?.description || '产地、处理法与烘焙，构成每一款豆子的风味个性。' }}</p>
        <div class="wheel-match-list"><button v-for="coffee in matches" :key="coffee.id" :aria-pressed="compareIds.includes(coffee.id)" :disabled="compareIds.length === 4 && !compareIds.includes(coffee.id)" @click="emit('toggle', coffee)"><span>{{ coffee.name }}<small>{{ coffee.process }} · {{ selectedFlavor ? `${coffee.flavors[selectedFlavor]}/5` : coffee.roast }}</small></span><b>{{ compareIds.includes(coffee.id) ? '✓' : '+' }}</b></button></div>
        <button class="line-button" :disabled="!props.matches.length" @click="emit('compare')">用匹配样本对比 <span>→</span></button>
      </div>
      <div class="wheel-families panel-line"><p class="kicker">风味分类</p><div v-for="category in categories" :key="category.name" class="wheel-family"><h3><i :style="{ background: colors[category.name] || category.color }"></i>{{ category.name }}</h3><div><button v-for="tag in tags.filter(t => t.category === category.name)" :key="tag.id" :class="{ selected: selectedFlavor === tag.id }" :aria-pressed="selectedFlavor === tag.id" @click="emit('flavor', tag.id)">{{ tag.name }}</button></div></div></div>
    </aside>
  </div>
</template>

<style scoped>
.wheel-stage { min-height: 0; aspect-ratio: 1; max-width: 570px; margin: 0 auto; }.wheel-stage svg { width: 100%; overflow: visible; }
.flavor-sector { cursor: pointer; outline: none; transform: translate(var(--shift-x, 0px), var(--shift-y, 0px)) scale(1); transform-box: view-box; transform-origin: 260px 260px; transition: transform .48s cubic-bezier(.16, 1, .3, 1), opacity .25s ease, filter .35s ease; }
.flavor-sector.raised { transform: translate(var(--shift-x), var(--shift-y)) scale(1.045); filter: drop-shadow(0 7px 8px rgb(32 45 39 / 18%)); }
.flavor-sector.active { animation: flavor-breathe 2.8s ease-in-out infinite; }
.flavor-sector:focus, .flavor-sector:focus-visible { outline: none; }
.sector-fill { fill-opacity: .83; transition: fill-opacity .25s ease, filter .35s ease; }.flavor-sector:hover .sector-fill, .flavor-sector:focus-visible .sector-fill, .flavor-sector.active .sector-fill { fill-opacity: 1; filter: saturate(1.12) brightness(1.04); }
.sector-outline { fill: none; stroke: #fffdf8; stroke-width: 2; pointer-events: none; transition: stroke .25s ease, stroke-width .25s ease; }.coffee-highlight .sector-outline, .active .sector-outline { stroke: #213b2d; stroke-width: 3; }.dimmed { opacity: .3; }
.sector-label { font: 700 14px var(--body); fill: #17261f; stroke: #fffdf8; stroke-width: 4px; paint-order: stroke fill; stroke-linejoin: round; pointer-events: none; }
.center-category { fill: #c0d5c9; font: 600 11px var(--body); }.center-name { fill: #fff; font: 700 25px var(--body); }.center-count { fill: #e2eadf; font: 12px var(--body); }
.wheel-coffee-context { color: var(--muted); text-align: center; margin: 0; font-size: 12px; }
.wheel-matches, .wheel-families { padding: 24px; }.match-total { display: flex; align-items: baseline; gap: 12px; }.match-total strong { font: 700 48px/1.1 var(--display); color: var(--coral); }.match-total span { font-size: 12px; color: var(--muted); }
.flavor-description { font-size: 12px; color: var(--muted); line-height: 1.8; min-height: 44px; }.wheel-match-list { margin: 12px 0 20px; }.wheel-match-list button { width: 100%; display: flex; align-items: center; gap: 16px; justify-content: space-between; background: transparent; text-align: left; border-top: 1px solid var(--line); padding: 12px 0; color: var(--ink); font-size: 12px; }.wheel-match-list button span { min-width: 0; overflow-wrap: anywhere; }.wheel-match-list small { display: block; color: var(--muted); margin-top: 5px; font-size: 10px; }.wheel-match-list b { font-size: 18px; color: var(--green); }
.wheel-family { margin-top: 15px; }.wheel-family h3 { display: flex; align-items: center; gap: 8px; font-size: 12px; margin: 0 0 6px; }.wheel-family i { width: 8px; height: 8px; }.wheel-family > div { display: flex; flex-wrap: wrap; gap: 14px; padding-left: 16px; }.wheel-family button { background: transparent; padding: 3px 0; color: var(--muted); font-size: 12px; border-bottom: 1px solid transparent; }.wheel-family button.selected { color: var(--green); border-color: var(--green); font-weight: 700; }
@media (max-width: 600px) { .wheel-panel { padding: 20px 12px; }.wheel-panel .subheading { flex-direction: row; gap: 8px; }.wheel-panel h2 { font-size: 20px; }.sector-label { font-size: 16px; } }
@keyframes flavor-breathe { 0%, 100% { transform: translate(var(--shift-x), var(--shift-y)) scale(1.045); } 50% { transform: translate(calc(var(--shift-x) * 1.08), calc(var(--shift-y) * 1.08)) scale(1.065); } }
@media (prefers-reduced-motion: reduce) { .flavor-sector, .flavor-sector.raised, .sector-fill, .sector-outline { animation: none; transition: none; transform: none; filter: none; } }
</style>
