import test from 'node:test';
import assert from 'node:assert/strict';
import { rankBeans } from '../src/beanMatching.js';

const coffees = [
  { id: 1, process: '水洗', roast: '浅烘', flavors: { citrus: 5 } },
  { id: 2, process: '日晒', roast: '中烘', flavors: { citrus: 2, berry: 2 } },
  { id: 3, process: '水洗', roast: '浅烘', flavors: { citrus: 4, berry: 3 } },
  { id: 4, process: '水洗', roast: '浅烘', flavors: { cocoa: 5 } },
  { id: 5, process: '水洗', roast: '浅烘', flavors: { citrus: 4, berry: 3 } }
];

test('ranks coverage before strength and preserves a stable tie order', () => {
  assert.deepEqual(rankBeans(coffees, ['citrus', 'berry']).map(item => item.coffee.id), [3, 5, 2, 1]);
  assert.deepEqual(rankBeans(coffees, ['citrus', 'berry'])[0].matches, [
    { id: 'citrus', intensity: 4 }, { id: 'berry', intensity: 3 }
  ]);
});

test('filters by process and roast, including an empty result', () => {
  assert.deepEqual(rankBeans(coffees, ['citrus', 'berry'], { process: '水洗', roast: '浅烘' }).map(item => item.coffee.id), [3, 5, 1]);
  assert.deepEqual(rankBeans(coffees, ['citrus'], { process: '日晒', roast: '浅烘' }), []);
  assert.deepEqual(rankBeans(coffees, [], {}), []);
});
