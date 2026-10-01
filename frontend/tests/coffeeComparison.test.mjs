import test from 'node:test';
import assert from 'node:assert/strict';
import { buildComparison, comparisonLineSegments, metadataRows, preferenceMatches, recordedIntensity } from '../src/coffeeComparison.js';

const tags = [
  { id: 'citrus', name: '柑橘', category: '水果' },
  { id: 'berry', name: '莓果', category: '水果' },
  { id: 'cocoa', name: '可可', category: '坚果可可' }
];
const beans = [
  { id: 1, country: 'China', process: '水洗', roast: '浅烘', flavors: { citrus: 5, berry: 3 } },
  { id: 2, country: 'Kenya', process: '水洗', roast: '中烘', flavors: { citrus: 2, cocoa: 4 } },
  { id: 3, country: 'Kenya', process: '日晒', roast: '浅烘', flavors: { citrus: 3 } }
];

test('lines connect adjacent readings and bridge gaps without inventing measurements', () => {
  assert.deepEqual(comparisonLineSegments([null, 5, 3, null, 2, null]), [
    { from: { index: 1, value: 5 }, to: { index: 2, value: 3 }, missing: false },
    { from: { index: 2, value: 3 }, to: { index: 4, value: 2 }, missing: true }
  ]);
  assert.deepEqual(comparisonLineSegments([]), []);
  assert.deepEqual(comparisonLineSegments([null, 4, null]), []);
  assert.deepEqual(comparisonLineSegments([null, null]), []);
});

test('unrecorded and invalid intensity are not converted into zero', () => {
  for (const value of [undefined, null, '', 0, -1, 6, 'bad', Infinity]) {
    assert.equal(recordedIntensity({ flavors: { citrus: value } }, 'citrus'), null);
  }
  assert.equal(recordedIntensity({ flavors: { citrus: '4' } }, 'citrus'), 4);
});

test('family strength is the peak of recorded tags, with missing cells retained', () => {
  const result = buildComparison(beans, tags, [{ name: '水果' }, { name: '坚果可可' }]);
  assert.deepEqual(result.families[0].cells.map(cell => cell.value), [5, 2, 3]);
  assert.deepEqual(result.families[1].cells.map(cell => cell.value), [null, 4, null]);
  assert.deepEqual(result.families[0].cells[0].tags, ['柑橘']);
});

test('shared and largest differences compare recorded values only', () => {
  const result = buildComparison(beans, tags);
  assert.deepEqual(result.shared.map(row => row.id), ['citrus']);
  assert.equal(result.biggestGap.id, 'citrus');
  assert.equal(result.biggestGap.gap, 3);
  assert.equal(result.rows.find(row => row.id === 'cocoa').gap, null);
  assert.deepEqual(result.signatures[0].unique.map(row => row.id), ['berry']);
});

test('empty and single-bean comparisons do not invent shared or unique findings', () => {
  assert.deepEqual(buildComparison([], tags).rows, []);
  const result = buildComparison([beans[0]], tags);
  assert.deepEqual(result.shared, []);
  assert.equal(result.biggestGap, null);
  assert.deepEqual(result.signatures[0].unique, []);
});

test('metadata highlights differences and keeps missing fields empty', () => {
  const rows = metadataRows(beans, country => ({ China: '中国', Kenya: '肯尼亚' })[country]);
  assert.deepEqual(rows.find(row => row.key === 'country').values, ['中国', '肯尼亚', '肯尼亚']);
  assert.equal(rows.find(row => row.key === 'roast').different, true);
  assert.deepEqual(rows.find(row => row.key === 'altitude').values, [null, null, null]);
  assert.equal(rows.find(row => row.key === 'altitude').different, false);
});

test('unknown tags are preserved and preference matches use actual observations', () => {
  const coffee = { id: 4, flavors: { unknown: 3, citrus: 4 } };
  assert.equal(buildComparison([coffee], tags).rows.find(row => row.id === 'unknown').category, '未分类');
  assert.deepEqual(preferenceMatches(coffee, ['citrus', 'cocoa']), [{ id: 'citrus', value: 4 }]);
});
