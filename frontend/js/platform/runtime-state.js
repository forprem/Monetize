export const DEFAULT_ZIPS = [];

const ZIP_COORDS = {
  '10001': { lat: 40.7506, lon: -73.9972 },
  '30301': { lat: 33.7529, lon: -84.3925 },
  '60601': { lat: 41.8858, lon: -87.6229 },
  '94105': { lat: 37.7898, lon: -122.3942 },
  '75201': { lat: 32.7876, lon: -96.7994 },
};

export function createRuntimeState() {
  return {
    compareResults: [],
    focusedZip: null,
    layerMode: 'composite',
    exportsItems: [],
    activityItems: [],
    pagination: {
      exports: { limit: 10, offset: 0, returned: 0 },
      audit: { limit: 8, offset: 0, returned: 0 },
    },
    autoRefreshTimer: null,
  };
}

export function colorForScore(score) {
  if (score >= 80) return '#2c8e58';
  if (score >= 72) return '#c4862e';
  return '#c5543c';
}

function hashZipToCoord(zip) {
  const num = Number(zip.replace(/\D/g, '')) || 10000;
  const lat = 25 + ((num % 2400) / 2400) * 24;
  const lon = -124 + (((Math.floor(num / 3)) % 5800) / 5800) * 58;
  return { lat, lon };
}

export function getCoord(zip) {
  return ZIP_COORDS[zip] || hashZipToCoord(zip);
}
