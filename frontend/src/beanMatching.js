export function rankBeans(coffees, flavorIds, { process = 'all', roast = 'all' } = {}) {
  if (!flavorIds.length) return [];
  return coffees
    .filter(coffee => (process === 'all' || coffee.process === process) && (roast === 'all' || coffee.roast === roast))
    .map(coffee => {
      const matches = flavorIds.map(id => ({ id, intensity: Number(coffee.flavors?.[id] || 0) }))
        .filter(match => match.intensity > 0);
      return {
        coffee,
        matches,
        coverage: matches.length,
        strength: matches.reduce((total, match) => total + match.intensity, 0)
      };
    })
    .filter(result => result.coverage > 0)
    .sort((a, b) => b.coverage - a.coverage || b.strength - a.strength || a.coffee.id - b.coffee.id);
}
