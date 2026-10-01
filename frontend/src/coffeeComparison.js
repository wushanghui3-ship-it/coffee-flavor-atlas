export function recordedIntensity(coffee, id) {
  const raw = coffee.flavors?.[id];
  if (raw == null || raw === '') return null;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 1 && value <= 5 ? value : null;
}

export function comparisonLineSegments(values) {
  const segments = [];
  let previous = null;
  values.forEach((value, index) => {
    if (value === null) return;
    if (previous) segments.push({ from: previous, to: { index, value }, missing: index - previous.index > 1 });
    previous = { index, value };
  });
  return segments;
}

export function buildComparison(coffees, tags, categories = []) {
  const tagMap = new Map(tags.map(tag => [tag.id, tag]));
  const ids = new Set(coffees.flatMap(coffee => Object.keys(coffee.flavors || {})));
  const rows = [...ids].map(id => {
    const tag = tagMap.get(id) || { id, name: id, category: '未分类' };
    const values = coffees.map(coffee => recordedIntensity(coffee, id));
    const known = values.filter(value => value !== null);
    return {
      ...tag, values,
      shared: coffees.length > 1 && known.length === coffees.length,
      gap: known.length > 1 ? Math.max(...known) - Math.min(...known) : null,
      peak: known.length ? Math.max(...known) : null
    };
  }).filter(row => row.peak !== null).sort((a, b) => a.category.localeCompare(b.category, 'zh-CN') || a.name.localeCompare(b.name, 'zh-CN'));

  const familyNames = [...new Set([...categories.map(category => category.name), ...rows.map(row => row.category)])];
  const families = familyNames.map(name => {
    const members = rows.filter(row => row.category === name);
    const cells = coffees.map((_, index) => {
      const known = members.filter(row => row.values[index] !== null);
      const peak = known.length ? Math.max(...known.map(row => row.values[index])) : null;
      return { value: peak, tags: known.filter(row => row.values[index] === peak).map(row => row.name) };
    });
    return { name, cells };
  }).filter(family => family.cells.some(cell => cell.value !== null));

  const shared = rows.filter(row => row.shared).sort((a, b) => b.peak - a.peak);
  const biggestGap = rows.filter(row => row.gap > 0).sort((a, b) => b.gap - a.gap || a.name.localeCompare(b.name, 'zh-CN'))[0] || null;
  const signatures = coffees.map((coffee, index) => {
    const own = rows.filter(row => row.values[index] !== null).sort((a, b) => b.values[index] - a.values[index]);
    const unique = coffees.length > 1 ? own.filter(row => row.values.every((value, other) => other === index || value === null)) : [];
    return { coffee, top: own.slice(0, 3), unique: unique.slice(0, 2) };
  });
  return { rows, families, shared, biggestGap, signatures };
}

export function preferenceMatches(coffee, flavorIds) {
  return flavorIds.map(id => ({ id, value: recordedIntensity(coffee, id) })).filter(match => match.value !== null);
}

export function metadataRows(coffees, countryLabel = country => country) {
  const fields = [
    ['country', '产国'], ['region', '产区'], ['species', '豆种'], ['variety', '品种'],
    ['process', '处理法'], ['roast', '烘焙度'], ['altitude', '海拔'], ['year', '产季'], ['dataSource', '资料来源']
  ];
  return fields.map(([key, label]) => {
    const values = coffees.map(coffee => {
      const value = coffee[key];
      if (value == null || String(value).trim() === '') return null;
      return key === 'country' ? countryLabel(value) : String(value).trim();
    });
    return { key, label, values, different: new Set(values).size > 1 };
  });
}
