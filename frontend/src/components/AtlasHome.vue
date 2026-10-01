<script setup>
import { ref } from 'vue';

const props = defineProps({
  profiles: Object,
  profileCounts: { type: Object, default: () => ({}) },
  sampleCount: Number,
  countryCount: Number
});
const emit = defineEmits(['start', 'navigate']);
const activeFlavor = ref('default');
const previewFlavor = ref('default');
const flavorBackgrounds = {
  default: '/images/coffee-hero.jpg',
  bright: '/images/taste/bright.jpg',
  sweet: '/images/taste/sweet.jpg',
  rich: '/images/taste/cocoa.jpg'
};
const flavorLabels = {
  default: '新鲜烘焙的咖啡豆',
  bright: '明亮的柑橘与咖啡豆',
  sweet: '温暖甜感与咖啡豆',
  rich: '深色可可与咖啡豆'
};

function preview(key) { previewFlavor.value = key; }
function restoreActive() { previewFlavor.value = activeFlavor.value; }
function chooseFlavor(key) {
  activeFlavor.value = key;
  previewFlavor.value = key;
  emit('start', key);
}
function matchedCount(key) {
  return key === 'default' ? props.sampleCount : (props.profileCounts[key] || 0);
}
</script>

<template>
  <section class="atlas-home page-enter">
    <div class="atlas-home-hero" :class="`taste-${previewFlavor}`">
      <img v-for="(source, key) in flavorBackgrounds" :key="key" :src="source" :alt="flavorLabels[key]" class="atlas-home-photo" :class="{ active: previewFlavor === key }" :fetchpriority="key === 'default' ? 'high' : 'auto'" />
      <div class="atlas-home-copy">
        <p class="atlas-home-eyebrow">COFFEE ATLAS</p>
        <h1>咖啡风味图谱</h1>
        <p class="atlas-home-subtitle">下一杯，从喜欢的风味开始。</p>
        <div class="atlas-home-keywords" aria-label="按口味找豆">
          <button v-for="(profile, key) in profiles" :key="key" :class="{ active: activeFlavor === key }" @mouseenter="preview(key)" @mouseleave="restoreActive" @focus="preview(key)" @blur="restoreActive" @click="chooseFlavor(key)"><b>{{ profile.title }}</b><span>{{ profile.tags.map(id => ({ citrus: '柑橘', berry: '莓果', jasmine: '花香', brownSugar: '红糖', stone: '核果', almond: '杏仁', cocoa: '可可', cinnamon: '香料' })[id]).join(' · ') }}</span><small>{{ matchedCount(key) }} 款匹配样本</small><i aria-hidden="true">↗</i></button>
        </div>
      </div>
      <div class="atlas-home-caption"><span>ORIGIN. FLAVOR. YOUR CUP.</span><span>{{ matchedCount(previewFlavor) }} 款匹配样本 / {{ countryCount }} 个产国</span></div>
    </div>
    <div class="atlas-home-more">
      <div><p class="kicker">从产地到你的杯中</p><h2>每一款咖啡，都有自己的风味坐标。</h2></div>
      <div class="atlas-home-links"><button @click="emit('navigate', 'beans')">浏览豆库 <span>↗</span></button><button @click="emit('navigate', 'map')">走进产地 <span>↗</span></button></div>
    </div>
  </section>
</template>

<style scoped>
.atlas-home { --home-white: #fff; --home-mint: #d9eddf; background: #f7faf7; }
.atlas-home-hero { position: relative; isolation: isolate; height: min(760px, calc(100svh - 170px)); min-height: 440px; display: flex; align-items: center; overflow: hidden; background: #343e39; }
.atlas-home-photo { position: absolute; inset: 0; z-index: -2; width: 100%; height: 100%; object-fit: cover; object-position: center 55%; opacity: 0; transform: scale(1.035); transition: opacity .75s ease, transform 1.1s cubic-bezier(.16,1,.3,1); }
.atlas-home-photo.active { opacity: 1; transform: scale(1); }
.atlas-home-hero::before { content: ''; position: absolute; inset: 0; z-index: -1; background: rgb(15 25 21 / 48%); transition: background-color .65s ease; }
.atlas-home-hero.taste-bright::before { background: rgb(34 47 34 / 38%); }
.atlas-home-hero.taste-sweet::before { background: rgb(67 45 26 / 43%); }
.atlas-home-hero.taste-rich::before { background: rgb(19 16 14 / 55%); }
.atlas-home-copy { width: min(1380px, 90%); margin: 0 auto; color: var(--home-white); padding-bottom: 30px; }
.atlas-home-eyebrow { margin: 0 0 22px; font: 600 14px var(--mono); letter-spacing: 0; color: var(--home-mint); }
h1 { margin: 0; font: 800 72px/1.2 var(--display); letter-spacing: 0; }
.atlas-home-subtitle { margin: 18px 0 44px; font-size: 21px; }
.atlas-home-keywords { display: flex; flex-wrap: wrap; gap: 22px; max-width: 750px; }
.atlas-home-keywords button { flex: 1; min-width: 185px; position: relative; display: grid; text-align: left; gap: 5px; min-height: 112px; padding: 14px 26px 14px 0; background: transparent; color: var(--home-white); border-top: 1px solid rgb(255 255 255 / 65%); transition: transform .3s ease, border-color .3s ease, opacity .3s ease; }
.atlas-home-keywords button:hover, .atlas-home-keywords button:focus-visible { transform: translateY(-6px); border-color: #fff; }
.atlas-home-keywords button:not(.active) { opacity: .78; }
.atlas-home-keywords button.active { border-color: #fff; opacity: 1; }
.atlas-home-keywords button b { font-size: 21px; }
.atlas-home-keywords button span { font-size: 13px; color: var(--home-mint); }
.atlas-home-keywords button small { color: rgb(255 255 255 / 78%); font: 10px var(--mono); }
.atlas-home-keywords button i { position: absolute; right: 0; top: 12px; font-size: 23px; font-style: normal; }
.atlas-home-caption { position: absolute; bottom: 24px; left: 5%; right: 5%; display: flex; justify-content: space-between; gap: 12px; font: 500 11px var(--mono); color: #fff; }
.atlas-home-more { width: min(1380px, 90%); margin: 0 auto; padding: 38px 0 48px; display: flex; justify-content: space-between; align-items: center; gap: 24px; }
.atlas-home-more h2 { margin: 0; font: 700 24px/1.5 var(--display); }
.atlas-home-links { display: flex; gap: 28px; flex-shrink: 0; }
.atlas-home-links button { display: flex; align-items: center; gap: 22px; min-height: 44px; padding: 0; color: var(--green); background: transparent; border-bottom: 1px solid var(--green); }
@media (max-width: 900px) { h1 { font-size: 56px; }.atlas-home-copy { padding-bottom: 20px; }.atlas-home-more { align-items: flex-start; flex-direction: column; } }
@media (max-width: 600px) { .atlas-home-hero { height: calc(100svh - 145px); min-height: 420px; }.atlas-home-copy { width: 88%; }h1 { font-size: 38px; }.atlas-home-subtitle { font-size: 16px; margin: 14px 0 24px; }.atlas-home-keywords { flex-direction: column; gap: 10px; }.atlas-home-keywords button { min-height: 82px; padding: 10px 28px 10px 0; gap: 2px; }.atlas-home-keywords button b { font-size: 18px; }.atlas-home-caption { bottom: 16px; font-size: 9px; }.atlas-home-caption > span:first-child { display: none; }.atlas-home-more { padding-top: 24px; }.atlas-home-more h2 { font-size: 20px; } }
@media (prefers-reduced-motion: reduce) { .atlas-home-photo, .atlas-home-hero::before, .atlas-home-keywords button { transition: none; transform: none !important; } }
</style>
