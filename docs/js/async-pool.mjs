// WTMM: concurrency-limited async mapping with stable output order.
// Prevents expensive request bursts without dropping any work or changing content.
export async function mapWithConcurrency(items, limit, mapper) {
  if (!Array.isArray(items) || typeof mapper !== "function") {
    throw new TypeError("Expected items and async mapper");
  }
  if (!Number.isInteger(limit) || limit < 1) {
    throw new RangeError("Concurrency limit must be a positive integer");
  }
  const results = new Array(items.length);
  let next = 0;
  const worker = async () => {
    while (next < items.length) {
      const index = next++;
      results[index] = await mapper(items[index], index);
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}
