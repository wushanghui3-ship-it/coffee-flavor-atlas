<script setup>
import { onBeforeUnmount, ref } from 'vue';
import BeanImage from './BeanImage.vue';
const props = defineProps({ coffee: { type: Object, required: true } });
const emit = defineEmits(['saved']);
const file = ref(null);
const preview = ref('');
const input = ref(null);
const busy = ref(false);
const error = ref('');
const saved = ref(false);
function clear() {
  if (preview.value) URL.revokeObjectURL(preview.value);
  preview.value = ''; file.value = null;
  if (input.value) input.value.value = '';
}
function choose(event) {
  const selected = event.target.files?.[0];
  clear(); error.value = ''; saved.value = false;
  if (!selected) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(selected.type)) { error.value = '只支持 JPG、PNG 或 WebP 图片'; return; }
  if (selected.size > 6 * 1024 * 1024) { error.value = '图片不能超过 6 MB'; return; }
  file.value = selected; preview.value = URL.createObjectURL(selected);
}
async function save(remove = false) {
  busy.value = true; error.value = ''; saved.value = false;
  try {
    const response = await fetch(`/api/samples/${props.coffee.id}/image`, { method: remove ? 'DELETE' : 'PUT', ...(remove ? {} : { headers: { 'Content-Type': file.value.type }, body: file.value }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '图片保存失败');
    emit('saved', data); clear(); saved.value = true;
  } catch (failure) { error.value = failure.message; }
  finally { busy.value = false; }
}
onBeforeUnmount(clear);
</script>
<template>
  <div class="sample-image-editor">
    <BeanImage :coffee="{ ...coffee, imageUrl: preview || coffee.imageUrl }" />
    <div><label>样本图片 · JPG / PNG / WebP，最多 6 MB<input ref="input" type="file" accept="image/jpeg,image/png,image/webp" :disabled="busy" @change="choose" /></label>
      <div class="sample-image-actions"><button v-if="file" class="primary-button" type="button" :disabled="busy" @click="save()">{{ busy ? '保存中…' : '保存图片' }}</button><button v-if="file" class="text-button" type="button" :disabled="busy" @click="clear">取消</button><button v-else-if="coffee.imageUrl" class="text-button" type="button" :disabled="busy" @click="save(true)">移除图片</button><span v-if="saved" class="image-saved" role="status">图片已保存</span></div>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    </div>
  </div>
</template>
<style scoped>
.sample-image-editor { display: grid; grid-template-columns: 160px minmax(0, 1fr); align-items: center; gap: 22px; margin-top: 10px; padding: 20px 0; border-top: 1px solid var(--line); }
label { display: grid; gap: 10px; color: #52645a; font-size: 13px; }input { max-width: 100%; font-size: 12px; }input::file-selector-button { min-height: 40px; padding: 8px 12px; margin-right: 10px; border: 1px solid var(--line); background: var(--paper); color: var(--green); cursor: pointer; }
.sample-image-actions { display: flex; align-items: center; gap: 18px; margin-top: 12px; }.image-saved { color: var(--green); font-size: 12px; }
@media (max-width: 600px) { .sample-image-editor { grid-template-columns: 1fr; }.sample-image-editor :deep(.bean-image) { width: 160px; } }
</style>
