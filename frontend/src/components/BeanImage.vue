<script setup>
import { ref, watch } from 'vue';
const props = defineProps({ coffee: { type: Object, required: true } });
const failed = ref(false);
watch(() => props.coffee.imageUrl, () => { failed.value = false; });
</script>
<template>
  <div class="bean-image" :class="{ 'no-image': !coffee.imageUrl || failed }">
    <img v-if="coffee.imageUrl && !failed" :src="coffee.imageUrl" :alt="`${coffee.name}的样本图片`" loading="lazy" @error="failed = true" />
    <span v-else>{{ failed ? '图片暂时无法加载' : '样本图片待补充' }}</span>
  </div>
</template>
<style scoped>
.bean-image { width: 100%; aspect-ratio: 16 / 10; overflow: hidden; background: #e8eee9; }
.bean-image img { display: block; width: 100%; height: 100%; object-fit: cover; transition: transform .5s ease; }
.bean-image.no-image { display: grid; place-items: center; background: #e8eee9; color: #65746b; font-size: 12px; }
@media (prefers-reduced-motion: reduce) { .bean-image img { transition: none; } }
</style>
