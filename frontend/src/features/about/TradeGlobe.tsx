/* eslint-disable @typescript-eslint/ban-ts-comment -- coastline indexing predates noUncheckedIndexedAccess */
// @ts-nocheck
// Canvas 2D only — no Three.js. Conceptual visualization, not live trade data.
import { useEffect, useRef } from 'react'

type City = { name: string; lon: number; lat: number }
type Pt = number[]
type Shape = { pts: Pt[]; x0: number; x1: number; y0: number; y1: number }
type V3 = [number, number, number]

/* ───────────────────────── Geography ───────────────────────── */

const shape = (pts: Pt[]): Shape => {
  let x0 = Infinity
  let x1 = -Infinity
  let y0 = Infinity
  let y1 = -Infinity
  for (const [x, y] of pts) {
    if (x < x0) x0 = x
    if (x > x1) x1 = x
    if (y < y0) y0 = y
    if (y > y1) y1 = y
  }
  return { pts, x0, x1, y0, y1 }
}

const contains = (s: Shape, lon: number, lat: number) => {
  if (lon < s.x0 || lon > s.x1 || lat < s.y0 || lat > s.y1) return false
  const p = s.pts
  let inside = false
  for (let i = 0, j = p.length - 1; i < p.length; j = i++) {
    const xi = p[i][0]
    const yi = p[i][1]
    const xj = p[j][0]
    const yj = p[j][1]
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}

// Simplified coastlines (lon, lat). Enough detail for a dotted globe.
const LAND: Shape[] = [
  // Eurasia (with Arabia, India, SE Asia, Scandinavia)
  [[-5.5,36],[-2,36.7],[0,38.7],[0.5,40.5],[3,42],[4.5,43.4],[7,43.7],[7.5,44],[13.7,45.6],[14,45.2],[15.5,44],[17.5,42.8],[19.5,41.8],[19.5,40],[21,38.8],[21.5,36.8],[23,36.5],[23.8,38],[22.8,40.3],[24,40.8],[26,40.8],[26.3,40.1],[26.3,38.5],[27.3,37],[28.5,36.7],[30.5,36.6],[32.5,36.1],[34.5,36.8],[36,36.7],[35.8,35],[35.3,33.5],[34.5,31.5],[34.9,29.5],[35,28],[37,25],[39,21.5],[41.2,19],[42.8,15],[43.3,12.7],[45,12.8],[49,14.2],[52,16],[55.5,17.5],[57.7,19],[58.6,20.5],[59.8,22.4],[58.8,23.5],[56.4,24.5],[56.3,26.2],[55.2,25.3],[54,24.2],[51.6,24.3],[51.6,25.9],[51.2,26.1],[50.8,25.5],[50.9,24.7],[50.2,26.5],[49.5,27.5],[48.5,28.5],[48,29.9],[48.5,30.1],[50.2,30],[51.5,27.9],[54,26.7],[56.3,27.1],[57,25.7],[61,25.2],[66.5,25.3],[68.5,23.5],[70,21],[72.6,21.5],[72.8,19],[74.5,14.5],[76,10],[77.5,8.1],[79.8,10.3],[80,13],[80.2,15.5],[84,18],[86.5,20],[87,21.5],[90,22],[92,21],[94.3,19],[94,16],[97.5,16.5],[98.3,13],[98.5,8],[101,2.5],[103.5,1.4],[104.2,1.5],[103.4,4.5],[102,6.3],[100.3,7],[99.3,9.5],[100,12.5],[102.5,12],[104.8,10],[105,8.7],[106.5,10],[109,11.5],[109,15],[106.5,19.5],[108,21.5],[110.5,21],[112,22],[116,22.8],[119,25.2],[122,29.5],[121.5,31.5],[120.5,34],[119,35],[120.5,36.5],[122.5,37],[120,37.5],[118.5,38.2],[117.5,38.8],[118.5,39.2],[121,40.8],[121.7,39],[123,40],[125,39.5],[126.5,37.5],[126.5,34.5],[129.4,35.2],[128,38.5],[129.5,40.8],[131,42.5],[135,43.5],[140,48],[141,53],[137,54.5],[143,59.5],[151,59.5],[156,61.8],[160,61.5],[157.5,58],[156,55],[155.8,53],[156.7,51],[158.5,53],[162,55.5],[163.5,59.5],[165,60.5],[170,60],[178,64.5],[180,65.5],[180,69],[170,70],[160,69.5],[140,72.5],[128,73],[112,76],[100,77],[87,75],[80,73],[73,72.5],[68,69],[60,69],[54,68.5],[44,68],[41,66.5],[40,67.5],[33,69.3],[28,71],[20,70],[14,67.5],[10,64],[5,62],[5,59],[8,58],[10.5,59.3],[8.5,57],[8.2,55.5],[8.7,54],[5,53.3],[4,52],[2,51],[-1.5,49.7],[-4.5,48.5],[-1.5,46],[-2,43.5],[-9,43],[-9,37]],
  // Italy
  [[7,44],[10,44],[12,42],[15.5,40],[15.7,38],[16.5,38.5],[17.1,39.2],[16.5,40],[18.5,40.1],[16,41.8],[14,42.5],[12.5,44],[12.3,45.3],[13.7,45.6],[13,46],[7,45.9]],
  // Africa
  [[-5.5,35.8],[-2,35.2],[3,36.8],[10,37.3],[11,35],[10,33.5],[15,32.3],[20,32],[22,32.8],[25,31.6],[29,30.9],[32,31.3],[34,31.2],[32.5,30],[33.5,27.5],[35.5,24],[37.2,21],[38.5,18],[40,15.5],[43,12.7],[44.5,10.4],[51.3,11.8],[51,10],[48,5],[44,1.5],[41,-1.7],[39.2,-5],[39.5,-8.5],[40.5,-11],[40.5,-15],[35,-19.5],[35.5,-24],[32.8,-26],[32.9,-28.5],[30,-31.2],[26,-34],[20,-34.8],[18.4,-34],[17,-29],[15,-26.5],[14.5,-22.5],[11.7,-17],[13.5,-12],[12.3,-6],[9,-1],[9.5,3.8],[8.5,4.5],[5,6],[1,5.8],[-4,5.2],[-7.5,4.4],[-12,7.5],[-15,11],[-17.5,14.7],[-16.5,19.5],[-17,21],[-15,24.5],[-13,27.5],[-9.7,30],[-9.8,31.5],[-6.5,34]],
  // North America
  [[-168,66],[-156,71.3],[-141,69.7],[-128,70],[-115,68],[-100,68],[-95,69],[-83,69.5],[-82,69.5],[-75,68],[-65,62.5],[-62,58],[-57,54],[-60,50],[-66,50],[-64,46.5],[-67,45],[-70,43.5],[-70,41.7],[-74,40.5],[-76,38],[-75.5,35.2],[-78,34],[-81,31.5],[-80,27],[-80.2,25.2],[-81.2,25.2],[-82.8,28],[-84,30],[-87,30.4],[-89.5,30],[-90,29],[-93.8,29.7],[-97,27.5],[-97.5,24],[-97.8,22],[-96,19],[-94.5,18.2],[-91.5,18.6],[-90.5,21],[-87,21.5],[-87.5,18],[-88.5,16],[-84,15.8],[-83.5,11],[-81.5,9],[-79.5,9.5],[-77.5,8.5],[-79.5,7.2],[-83,8.3],[-85.7,10.8],[-87.5,13],[-91.5,14],[-94.5,16],[-97,15.8],[-101,17.3],[-105.5,20],[-105.6,22.8],[-109,25.5],[-112.5,29.5],[-114.7,31.7],[-114.5,30],[-112,25.5],[-110,23],[-112.5,24.7],[-115,28],[-117.1,32.5],[-120.5,34.5],[-122.5,37.5],[-124,40.5],[-124.2,46],[-123,48.3],[-125,50],[-128,51.5],[-130.5,54.7],[-134,57.5],[-137,58.7],[-140,59.7],[-146,60.8],[-150,59.5],[-152,58],[-157,56.5],[-162,55],[-158,58.5],[-162,58.5],[-165,60.5],[-165,62.5],[-161,64.5],[-166,64.5]],
  // South America
  [[-77.5,8.5],[-75,11],[-72,12],[-71,11],[-68,10.6],[-64,10.5],[-61,10.5],[-57,6],[-52.5,5],[-50,1.5],[-50,-0.5],[-44,-2.5],[-40,-3],[-35,-5.5],[-35,-9],[-39,-13.5],[-39,-18],[-41,-22],[-44,-23],[-48.5,-26],[-48.8,-28.5],[-52,-32],[-54,-34.8],[-57,-34.5],[-58.5,-34.3],[-57,-36.5],[-58,-38.5],[-62,-39],[-62.5,-41],[-65,-41],[-64.5,-42.5],[-65.5,-45],[-67.5,-46.5],[-66,-48],[-69,-51.5],[-68.5,-52.4],[-71,-54],[-74,-52],[-75.5,-47],[-74,-43],[-73.5,-37],[-71.5,-30],[-70.5,-23],[-70.2,-18.5],[-76,-14],[-79,-8],[-81,-5],[-80,-2],[-80,0.5],[-78.5,2],[-77.5,4],[-77.5,7]],
  // Greenland, Arctic islands, Iceland
  [[-73,78],[-60,82],[-30,83.5],[-18,80],[-20,75],[-22,70],[-32,68],[-42,60],[-47,61],[-53,66],[-55,70],[-60,76]],
  [[-80,73],[-68,70],[-62,66.5],[-66,62],[-73,64],[-78,65],[-90,72]],
  [[-118,72],[-105,73],[-100,70],[-112,69]],
  [[-90,80],[-70,83],[-62,81],[-78,77]],
  [[-24,65.5],[-22,66.4],[-15,66.3],[-13.5,65],[-18,63.4],[-22.5,63.8]],
  // British Isles
  [[-5.5,50],[1.5,51],[1.7,52.8],[-0.3,54.5],[-2,56],[-2,57.6],[-3.5,58.6],[-5.5,58.5],[-6,56.5],[-5,54.8],[-3,54],[-4.5,53.2],[-3,51.5]],
  [[-10,51.5],[-6,52],[-6,54.5],[-8,55.2],[-10,54]],
  // Japan, Sri Lanka, Philippines
  [[130.8,31],[131.5,33.5],[135,34],[136.8,34.5],[139.8,35],[141,38],[141.5,41],[140,40.5],[139.5,38],[136.5,37],[133,35.5],[131,34]],
  [[140,42],[141.5,43],[145.5,43.5],[142,45.5],[141.5,44]],
  [[79.8,9.5],[81.8,7.5],[80.5,6],[79.9,7.5]],
  [[120,18.5],[122.2,18.4],[122,14],[124,13],[121,13.8],[120,16]],
  [[122,7],[126.5,7.5],[126,6],[124,6.8]],
  // Indonesia
  [[95.3,5.5],[98,4],[104,-1.5],[106,-5.8],[102,-4],[98.5,0.5],[95.5,3]],
  [[105.3,-6.8],[108,-6.4],[114.5,-7.8],[114.5,-8.7],[106,-7.5]],
  [[109,1.5],[111,2],[113,3.5],[117,7],[119,5],[118,1],[117.5,-1],[116,-4],[114,-3.5],[110,-3],[109,-1]],
  [[119,-5],[120,1.2],[125,1.5],[121,-1.5],[123,-5]],
  [[131,-1],[135,-3.3],[141,-2.7],[147,-6],[150.5,-10.5],[143,-9],[138,-8],[134,-4]],
  // Oceania, Madagascar
  [[113.5,-22],[114,-26],[115,-34],[118,-35],[123.5,-34],[129,-31.5],[131.5,-31.5],[135,-34.8],[138,-35.5],[140,-38],[144,-38.5],[148,-37.8],[150,-37],[153,-31],[153.5,-27],[152.8,-25],[149,-21],[146,-18.8],[145.3,-15],[143.5,-14],[142.5,-10.8],[141.5,-13],[141,-17],[139,-17.5],[136,-15],[135.5,-12],[132.5,-11.5],[130,-12.5],[129.5,-15],[126,-14],[122,-17.5],[121,-19.5],[118,-20.3]],
  [[145,-41],[148.2,-41],[147,-43.5],[145.5,-42.5]],
  [[172.7,-34.5],[175,-37],[178,-37.7],[176,-41.5],[174.5,-41.3],[174.8,-39.5],[173,-35.5]],
  [[172.5,-40.6],[174,-41.5],[171,-44.5],[169,-46.6],[166.5,-46],[168,-44],[170.5,-42.5]],
  [[49.3,-12],[50.5,-15.5],[47.5,-25],[45,-25.5],[43.5,-22],[44.3,-16.5],[47.5,-15]],
].map(shape)

// Inland seas carved out of the land polygons.
const WATER: Shape[] = [
  // Caspian
  [[47,45],[49,46.5],[53,46.5],[53.5,45],[51.5,44],[50.5,45],[51.5,42.5],[53,41.5],[54,40.5],[53.8,37.2],[50.5,37],[49,38.5],[49,40.5],[48,41.8],[47.5,43.5]],
  // Black Sea
  [[28,41.2],[28,43.5],[29.7,45.2],[31,46.5],[33,46],[33.5,44.5],[36.5,45.3],[38,47],[39.2,47],[37.5,45],[40,43.5],[41.5,41.6],[38,41],[35,42],[31,41.1],[29,41.2]],
  // Baltic
  [[10,55.5],[13,56],[16,57],[19,60],[17,63],[21,65.5],[25,65.2],[22,62],[23,60],[29,60.5],[24,58],[21,57],[19,55],[14,54.2],[11,54.5]],
  // Hudson Bay
  [[-95,59],[-94,62],[-88,64],[-82,63.5],[-78,62.5],[-77,58],[-79,55],[-82,52.8],[-85,55.2],[-90,57],[-93,58.5]],
].map(shape)

/* ───────────────────────── Config ───────────────────────── */

const HUB: City = { name: 'شیراز', lon: 52.58, lat: 29.59 }
const PARTNERS: City[] = [
  { name: 'دبی، امارات', lon: 55.27, lat: 25.2 },
  { name: 'استانبول', lon: 28.97, lat: 41.01 },
  { name: 'مسکو', lon: 37.62, lat: 55.75 },
  { name: 'مومبای', lon: 72.87, lat: 19.07 },
  { name: 'پکن', lon: 116.4, lat: 39.9 },
  { name: 'فرانکفورت', lon: 8.68, lat: 50.11 },
  { name: 'تاشکند', lon: 69.24, lat: 41.3 },
]

const RAD = Math.PI / 180
const TAU = Math.PI * 2
const ARC_STEPS = 56
const TRAIL = 16
const TRAIL_SEGS = 7
const BUCKETS = 6
const LIGHT: V3 = [-0.45, 0.5, 0.74]
const FONT_SIZE_RATIO = 0.03

const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v))
const clamp01 = (v: number) => clamp(v, 0, 1)
const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2)

const toVec = (lon: number, lat: number): V3 => {
  const p = lat * RAD
  const l = lon * RAD
  return [Math.cos(p) * Math.sin(l), Math.sin(p), Math.cos(p) * Math.cos(l)]
}

const buildLand = (step: number): Float32Array => {
  const out: number[] = []
  let row = 0
  for (let lat = -56; lat <= 83; lat += step, row++) {
    const lonStep = step / Math.max(Math.cos(lat * RAD), 0.25)
    const offset = row % 2 ? lonStep / 2 : 0
    for (let lon = -180 + offset; lon < 180; lon += lonStep) {
      if (!LAND.some((s) => contains(s, lon, lat))) continue
      if (WATER.some((s) => contains(s, lon, lat))) continue
      const v = toVec(lon, lat)
      out.push(v[0], v[1], v[2])
    }
  }
  return new Float32Array(out)
}

const landCache = new Map<number, Float32Array>()
const getLand = (step: number) => {
  let land = landCache.get(step)
  if (!land) {
    land = buildLand(step)
    landCache.set(step, land)
  }
  return land
}

const buildArc = (a: V3, b: V3, lift: number): Float32Array => {
  const out = new Float32Array((ARC_STEPS + 1) * 3)
  const w = Math.acos(clamp(a[0] * b[0] + a[1] * b[1] + a[2] * b[2], -1, 1))
  const s = Math.sin(w) || 1
  for (let i = 0; i <= ARC_STEPS; i++) {
    const t = i / ARC_STEPS
    const k1 = Math.sin((1 - t) * w) / s
    const k2 = Math.sin(t * w) / s
    const h = 1 + lift * Math.sin(Math.PI * t)
    out[i * 3] = (a[0] * k1 + b[0] * k2) * h
    out[i * 3 + 1] = (a[1] * k1 + b[1] * k2) * h
    out[i * 3 + 2] = (a[2] * k1 + b[2] * k2) * h
  }
  return out
}

const buildGraticule = (): Float32Array[] => {
  const lines: Float32Array[] = []
  for (let lat = -60; lat <= 60; lat += 30) {
    const pts: number[] = []
    for (let lon = -180; lon <= 180; lon += 5) pts.push(...toVec(lon, lat))
    lines.push(new Float32Array(pts))
  }
  for (let lon = -180; lon < 180; lon += 30) {
    const pts: number[] = []
    for (let lat = -85; lat <= 85; lat += 5) pts.push(...toVec(lon, lat))
    lines.push(new Float32Array(pts))
  }
  return lines
}

const makeSprite = (rgb: string) => {
  const s = 64
  const c = document.createElement('canvas')
  c.width = s
  c.height = s
  const g = c.getContext('2d')
  if (g) {
    const gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2)
    gr.addColorStop(0, 'rgba(255,255,255,1)')
    gr.addColorStop(0.16, `rgba(${rgb},0.85)`)
    gr.addColorStop(0.5, `rgba(${rgb},0.2)`)
    gr.addColorStop(1, `rgba(${rgb},0)`)
    g.fillStyle = gr
    g.fillRect(0, 0, s, s)
  }
  return c
}

// Dot colours from dim teal to bright mint.
const BUCKET_COLORS = Array.from({ length: BUCKETS }, (_, i) => {
  const t = i / (BUCKETS - 1)
  const r = Math.round(55 + 95 * t)
  const g = Math.round(165 + 85 * t)
  const b = Math.round(170 + 50 * t)
  return `rgba(${r},${g},${b},${(0.16 + 0.8 * t).toFixed(2)})`
})
const TRAIL_COLORS = Array.from({ length: TRAIL_SEGS }, (_, i) => {
  const t = i / (TRAIL_SEGS - 1)
  return `rgb(${Math.round(63 + 170 * t)},${Math.round(217 + 38 * t)},${Math.round(168 + 77 * t)})`
})

/* ───────────────────────── Component ───────────────────────── */

export function TradeGlobe() {
  const hostRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const host = hostRef.current
    const canvas = canvasRef.current
    if (!host || !canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const fontFamily = getComputedStyle(host).fontFamily || 'sans-serif'

    // ── static data (built once) ──
    const hub = toVec(HUB.lon, HUB.lat)
    const arcs = PARTNERS.map((c, i) => {
      const b = toVec(c.lon, c.lat)
      const w = Math.acos(clamp(hub[0] * b[0] + hub[1] * b[1] + hub[2] * b[2], -1, 1))
      return {
        pts: buildArc(hub, b, 0.07 + 0.3 * (w / Math.PI) + (i % 3) * 0.03),
        period: 5.4 + ((i * 7) % 5) * 0.45,
        delay: i * 1.3,
      }
    })
    const graticule = buildGraticule()
    const glowEmerald = makeSprite('63,217,168')

    // ── size dependent state ──
    let size = 0
    let dpr = 1
    let R = 0
    let dotSize = 1.5
    let lite = false
    let land: Float32Array = new Float32Array(0)
    let twinkleIdx: Int32Array = new Int32Array(0)
    let twinklePhase: Float32Array = new Float32Array(0)
    let bucketXY: Float32Array[] = []
    const bucketCount = new Int32Array(BUCKETS)
    let back: HTMLCanvasElement | null = null
    let front: HTMLCanvasElement | null = null
    const labelWidths = new Map<string, number>()

    // scratch (no per-frame allocation)
    const PX = new Float32Array(ARC_STEPS + 1)
    const PY = new Float32Array(ARC_STEPS + 1)
    const PZ = new Float32Array(ARC_STEPS + 1)
    const PV = new Uint8Array(ARC_STEPS + 1)
    const labels = PARTNERS.map(() => ({ on: false, x: 0, y: 0, a: 0, below: false }))
    let cl = 1
    let sl = 0
    let cp = 1
    let sp = 0
    let ox = 0
    let oy = 0
    let oz = 0
    let or2 = 0

    // ── view state ──
    let viewLon = reduced ? HUB.lon - 4 : HUB.lon + 28
    let viewLat = 22
    let time = 0

    const setView = () => {
      const l0 = viewLon * RAD
      const p0 = viewLat * RAD
      cl = Math.cos(l0)
      sl = Math.sin(l0)
      cp = Math.cos(p0)
      sp = Math.sin(p0)
    }

    // Writes screen position into ox/oy and depth into oz (no allocation).
    const proj = (x: number, y: number, z: number) => {
      const x1 = x * cl - z * sl
      const z1 = x * sl + z * cl
      const y2 = y * cp - z1 * sp
      oz = y * sp + z1 * cp
      or2 = x1 * x1 + y2 * y2
      ox = size / 2 + x1 * R
      oy = size / 2 - y2 * R
    }

    const makeLayer = () => {
      const c = document.createElement('canvas')
      c.width = canvas.width
      c.height = canvas.height
      const g = c.getContext('2d')
      if (g) g.setTransform(dpr, 0, 0, dpr, 0, 0)
      return { c, g }
    }

    const buildLayers = () => {
      const c = size / 2
      const a = makeLayer()
      const b = makeLayer()
      back = a.c
      front = b.c

      if (a.g) {
        const g = a.g
        const halo = (r0: number, r1: number, alpha: number, rgb: string) => {
          const gr = g.createRadialGradient(c, c, r0, c, c, r1)
          gr.addColorStop(0, `rgba(${rgb},${alpha})`)
          gr.addColorStop(1, `rgba(${rgb},0)`)
          g.fillStyle = gr
          g.beginPath()
          g.arc(c, c, r1, 0, TAU)
          g.fill()
        }
        halo(R * 0.9, R * 1.32, 0.16, '63,217,168')
        halo(R * 0.97, R * 1.18, 0.24, '125,226,255')
        halo(R * 0.99, R * 1.06, 0.3, '170,240,255')
        const body = g.createRadialGradient(c - R * 0.38, c - R * 0.42, R * 0.05, c, c, R * 1.02)
        body.addColorStop(0, '#2b6caa')
        body.addColorStop(0.35, '#17428a')
        body.addColorStop(0.7, '#0c2263')
        body.addColorStop(1, '#060d38')
        g.fillStyle = body
        g.beginPath()
        g.arc(c, c, R, 0, TAU)
        g.fill()
      }

      if (b.g) {
        const g = b.g
        g.save()
        g.beginPath()
        g.arc(c, c, R, 0, TAU)
        g.clip()
        const sx = c - R * 0.5
        const sh = g.createRadialGradient(sx, sx, R * 0.4, sx, sx, R * 2)
        sh.addColorStop(0, 'rgba(3,8,32,0)')
        sh.addColorStop(0.55, 'rgba(3,8,32,0.12)')
        sh.addColorStop(1, 'rgba(3,8,32,0.78)')
        g.fillStyle = sh
        g.fillRect(0, 0, size, size)
        const rim = g.createRadialGradient(c, c, R * 0.72, c, c, R)
        rim.addColorStop(0, 'rgba(110,235,215,0)')
        rim.addColorStop(0.85, 'rgba(110,235,215,0.06)')
        rim.addColorStop(1, 'rgba(140,240,255,0.36)')
        g.fillStyle = rim
        g.fillRect(0, 0, size, size)
        const hx = c - R * 0.45
        const hy = c - R * 0.5
        const spec = g.createRadialGradient(hx, hy, 0, hx, hy, R * 0.55)
        spec.addColorStop(0, 'rgba(255,255,255,0.1)')
        spec.addColorStop(1, 'rgba(255,255,255,0)')
        g.fillStyle = spec
        g.fillRect(0, 0, size, size)
        g.restore()
        g.strokeStyle = 'rgba(150,235,255,0.38)'
        g.lineWidth = 1.2
        g.beginPath()
        g.arc(c, c, R, 0, TAU)
        g.stroke()
      }
    }

    const configure = () => {
      const next = Math.floor(Math.min(host.clientWidth, host.clientHeight))
      if (next <= 0) return false
      const coarse = window.matchMedia('(pointer: coarse)').matches
      const weak = (navigator.hardwareConcurrency || 8) <= 4
      const nextLite = coarse || weak || next < 340
      const nextDpr = Math.min(window.devicePixelRatio || 1, nextLite ? 1.5 : 2)
      if (next === size && nextDpr === dpr && nextLite === lite) return false

      size = next
      dpr = nextDpr
      R = size * 0.38
      dotSize = clamp(size / 250, 1.25, 2.3)
      canvas.width = Math.round(size * dpr)
      canvas.height = Math.round(size * dpr)
      labelWidths.clear()

      if (nextLite !== lite || land.length === 0) {
        lite = nextLite
        land = getLand(lite ? 2.4 : 1.6)
        bucketXY = Array.from({ length: BUCKETS }, () => new Float32Array((land.length / 3) * 2))
        const n = Math.floor(land.length / 3)
        const picks: number[] = []
        for (let i = 0; i < n; i += 19) picks.push(i)
        twinkleIdx = Int32Array.from(picks)
        twinklePhase = Float32Array.from(picks, (i) => (i * 2.399) % TAU)
      }
      buildLayers()
      return true
    }

    /* ── drawing ── */

    const roundRectPath = (x: number, y: number, w: number, h: number, r: number) => {
      ctx.beginPath()
      if (typeof ctx.roundRect === 'function') ctx.roundRect(x, y, w, h, r)
      else ctx.rect(x, y, w, h)
    }

    const drawLabel = (text: string, x: number, y: number, alpha: number, strong: boolean, below: boolean) => {
      if (alpha <= 0.02) return
      const fs = Math.max(10.5, size * FONT_SIZE_RATIO)
      ctx.font = `${strong ? 700 : 600} ${fs}px ${fontFamily}`
      let tw = labelWidths.get(text)
      if (tw === undefined) {
        tw = ctx.measureText(text).width
        labelWidths.set(text, tw)
      }
      const h = fs * 1.9
      const bw = tw + 22
      const lx = clamp(x, bw / 2 + 4, size - bw / 2 - 4)
      const dist = (strong ? 26 : 22) * (size / 430)
      const ly = clamp(y + (below ? dist : -dist), h / 2 + 4, size - h / 2 - 4)

      ctx.save()
      ctx.globalAlpha = alpha
      ctx.strokeStyle = 'rgba(150,235,220,0.5)'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(lx, ly + (below ? -h / 2 : h / 2))
      ctx.stroke()
      roundRectPath(lx - bw / 2, ly - h / 2, bw, h, h / 2)
      ctx.fillStyle = 'rgba(7,17,56,0.9)'
      ctx.fill()
      ctx.strokeStyle = strong ? 'rgba(90,225,185,0.8)' : 'rgba(190,225,255,0.3)'
      ctx.stroke()
      ctx.direction = 'rtl'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#eef6ff'
      ctx.fillText(text, lx, ly + 1)
      ctx.restore()
    }

    const drawGraticule = () => {
      ctx.lineWidth = 0.8
      ctx.strokeStyle = 'rgba(140,200,245,0.11)'
      ctx.beginPath()
      for (const line of graticule) {
        let pen = false
        for (let i = 0; i < line.length; i += 3) {
          proj(line[i], line[i + 1], line[i + 2])
          if (oz > 0) {
            if (pen) ctx.lineTo(ox, oy)
            else ctx.moveTo(ox, oy)
            pen = true
          } else pen = false
        }
      }
      ctx.stroke()
    }

    const drawLand = (t: number) => {
      bucketCount.fill(0)
      const n = land.length
      for (let i = 0; i < n; i += 3) {
        const x = land[i]
        const y = land[i + 1]
        const z = land[i + 2]
        const x1 = x * cl - z * sl
        const z1 = x * sl + z * cl
        const y2 = y * cp - z1 * sp
        const z2 = y * sp + z1 * cp
        if (z2 <= 0.02) continue
        const light = x1 * LIGHT[0] + y2 * LIGHT[1] + z2 * LIGHT[2]
        const a = (0.35 + 0.65 * clamp01(light * 0.8 + 0.2)) * (0.3 + 0.7 * Math.sqrt(z2))
        const b = Math.min(BUCKETS - 1, (a * BUCKETS) | 0)
        const arr = bucketXY[b]
        const c = bucketCount[b]
        arr[c * 2] = size / 2 + x1 * R
        arr[c * 2 + 1] = size / 2 - y2 * R
        bucketCount[b] = c + 1
      }
      const s = dotSize
      for (let b = 0; b < BUCKETS; b++) {
        const c = bucketCount[b]
        if (!c) continue
        const arr = bucketXY[b]
        ctx.fillStyle = BUCKET_COLORS[b]
        ctx.beginPath()
        for (let j = 0; j < c; j++) ctx.rect(arr[j * 2] - s / 2, arr[j * 2 + 1] - s / 2, s, s)
        ctx.fill()
      }

      // sparse twinkling highlights
      for (let k = 0; k < twinkleIdx.length; k++) {
        const i = twinkleIdx[k] * 3
        proj(land[i], land[i + 1], land[i + 2])
        if (oz <= 0.12) continue
        const a = (0.5 + 0.5 * Math.sin(t * 1.5 + twinklePhase[k])) * 0.85 * clamp01(oz * 2)
        if (a < 0.05) continue
        ctx.fillStyle = `rgba(215,255,246,${a.toFixed(2)})`
        ctx.beginPath()
        ctx.arc(ox, oy, s * 0.8, 0, TAU)
        ctx.fill()
      }
    }

    const strokeRange = (from: number, to: number) => {
      ctx.beginPath()
      let pen = false
      for (let i = from; i <= to; i++) {
        if (PV[i]) {
          if (pen) ctx.lineTo(PX[i], PY[i])
          else ctx.moveTo(PX[i], PY[i])
          pen = true
        } else pen = false
      }
      ctx.stroke()
    }

    const glow = (sprite: HTMLCanvasElement, x: number, y: number, r: number, a: number) => {
      ctx.globalAlpha = a
      ctx.drawImage(sprite, x - r, y - r, r * 2, r * 2)
    }

    const drawArcs = (t: number, still: boolean) => {
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      const unit = size / 430

      for (let i = 0; i < arcs.length; i++) {
        const arc = arcs[i]
        const pts = arc.pts
        for (let s = 0; s <= ARC_STEPS; s++) {
          proj(pts[s * 3], pts[s * 3 + 1], pts[s * 3 + 2])
          PX[s] = ox
          PY[s] = oy
          PZ[s] = oz
          PV[s] = oz > 0 || or2 > 1 ? 1 : 0
        }
        const lbl = labels[i]
        lbl.on = false

        const p = still ? 0.6 : ((t + arc.delay) % arc.period) / arc.period
        const travel = p < 0.5 ? easeInOut(p / 0.5) : 1
        const energy = still ? 0.3 : p < 0.5 ? travel * 0.6 : 0.6 * (1 - clamp01((p - 0.5) / 0.3))

        // permanent faint arc
        ctx.globalAlpha = 0.16 + 0.3 * energy
        ctx.lineWidth = 1
        ctx.strokeStyle = 'rgb(125,226,255)'
        strokeRange(0, ARC_STEPS)

        const destVisible = PV[ARC_STEPS] === 1 && PZ[ARC_STEPS] > 0
        const face = clamp01((PZ[ARC_STEPS] - 0.1) * 4)
        const dx = PX[ARC_STEPS]
        const dy = PY[ARC_STEPS]

        // destination node
        if (destVisible) {
          ctx.globalAlpha = 0.9
          ctx.fillStyle = '#c5e4ff'
          ctx.beginPath()
          ctx.arc(dx, dy, Math.max(2, 2.6 * unit), 0, TAU)
          ctx.fill()
        }

        if (still) {
          if (destVisible) {
            lbl.on = true
            lbl.x = dx
            lbl.y = dy
            lbl.a = 0.85 * face
          }
          continue
        }

        // travelling comet
        if (p < 0.5) {
          const headF = travel * ARC_STEPS
          const tail = Math.max(0, headF - TRAIL)
          for (let s = 0; s < TRAIL_SEGS; s++) {
            const a0 = Math.floor(tail + ((headF - tail) * s) / TRAIL_SEGS)
            const a1 = Math.min(ARC_STEPS, Math.ceil(tail + ((headF - tail) * (s + 1)) / TRAIL_SEGS))
            ctx.globalAlpha = 0.12 + (0.8 * s) / TRAIL_SEGS
            ctx.lineWidth = (1 + s * 0.4) * Math.max(0.8, unit)
            ctx.strokeStyle = TRAIL_COLORS[s]
            strokeRange(a0, Math.max(a0, a1))
          }
          const h0 = Math.min(ARC_STEPS - 1, Math.floor(headF))
          if (PV[h0] && PV[h0 + 1]) {
            const f = headF - h0
            const hx = PX[h0] + (PX[h0 + 1] - PX[h0]) * f
            const hy = PY[h0] + (PY[h0 + 1] - PY[h0]) * f
            ctx.globalCompositeOperation = 'lighter'
            glow(glowEmerald, hx, hy, 15 * unit, 0.95)
            ctx.globalCompositeOperation = 'source-over'
            ctx.globalAlpha = 1
            ctx.fillStyle = '#f2fffb'
            ctx.beginPath()
            ctx.arc(hx, hy, Math.max(1.8, 2.2 * unit), 0, TAU)
            ctx.fill()
          }
        }

        // arrival pulse + label
        if (p >= 0.5 && destVisible) {
          const k = clamp01((p - 0.5) / 0.42)
          ctx.globalCompositeOperation = 'lighter'
          glow(glowEmerald, dx, dy, (10 + 16 * k) * unit, (1 - k) * 0.7)
          ctx.globalCompositeOperation = 'source-over'
          ctx.globalAlpha = (1 - k) * 0.75
          ctx.strokeStyle = 'rgb(110,235,200)'
          ctx.lineWidth = 1.4
          ctx.beginPath()
          ctx.arc(dx, dy, (4 + k * 22) * unit, 0, TAU)
          ctx.stroke()
          lbl.on = true
          lbl.x = dx
          lbl.y = dy
          lbl.a = clamp01(k * 5) * (1 - clamp01((k - 0.7) / 0.3)) * face
        }
      }
      ctx.globalAlpha = 1
    }

    const drawHubAndLabels = (t: number, still: boolean) => {
      const unit = size / 430
      proj(hub[0], hub[1], hub[2])
      const hx = ox
      const hy = oy
      const hz = oz
      const hubVisible = hz > 0

      // partner labels first, so the hub card stays on top
      for (let i = 0; i < PARTNERS.length; i++) {
        const l = labels[i]
        if (!l.on) continue
        drawLabel(PARTNERS[i].name, l.x, l.y, l.a, false, l.y >= hy)
      }

      if (!hubVisible) return
      const fade = clamp01(hz * 3)
      ctx.globalCompositeOperation = 'lighter'
      glow(glowEmerald, hx, hy, 34 * unit, 0.85 * fade)
      ctx.globalCompositeOperation = 'source-over'
      if (!still) {
        for (let r = 0; r < 2; r++) {
          const k = (t * 0.45 + r * 0.5) % 1
          ctx.globalAlpha = (1 - k) * 0.6 * fade
          ctx.strokeStyle = 'rgb(118,230,200)'
          ctx.lineWidth = 1.6
          ctx.beginPath()
          ctx.arc(hx, hy, (6 + k * 30) * unit, 0, TAU)
          ctx.stroke()
        }
      }
      ctx.globalAlpha = fade
      ctx.fillStyle = '#76ddc4'
      ctx.beginPath()
      ctx.arc(hx, hy, Math.max(4, 5.5 * unit), 0, TAU)
      ctx.fill()
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.arc(hx, hy, Math.max(1.8, 2.4 * unit), 0, TAU)
      ctx.fill()
      ctx.globalAlpha = 1
      drawLabel(HUB.name, hx, hy, fade, true, false)
    }

    const render = (t: number, still: boolean) => {
      if (!back || !front) return
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.globalAlpha = 1
      ctx.clearRect(0, 0, size, size)
      ctx.drawImage(back, 0, 0, size, size)
      setView()
      drawGraticule()
      drawLand(t)
      ctx.drawImage(front, 0, 0, size, size)
      drawArcs(t, still)
      drawHubAndLabels(t, still)
    }

    const reveal = () => {
      canvas.style.opacity = '1'
      host.dataset.ready = 'true'
    }

    /* ── lifecycle ── */

    configure()

    if (reduced) {
      render(0, true)
      reveal()
      const ro = new ResizeObserver(() => {
        if (configure()) render(0, true)
      })
      ro.observe(host)
      return () => {
        ro.disconnect()
        delete host.dataset.ready
      }
    }

    let raf = 0
    let running = false
    let inView = true
    let last = performance.now()

    const advance = (dt: number) => {
      const baseSpeed = lite ? 4.5 : 7 // degrees per second
      viewLon -= baseSpeed * dt
      viewLat = 22 + Math.sin(time * 0.12) * 3
    }

    const frame = (now: number) => {
      if (!running) return
      const dt = Math.min((now - last) / 1000, 0.05)
      last = now
      time += dt
      advance(dt)
      render(time, false)
      raf = requestAnimationFrame(frame)
    }
    const start = () => {
      if (running || document.hidden || !inView) return
      running = true
      last = performance.now()
      raf = requestAnimationFrame(frame)
    }
    const stop = () => {
      running = false
      cancelAnimationFrame(raf)
    }

    const io = new IntersectionObserver((entries) => {
      const e = entries[0]
      if (!e) return
      inView = e.isIntersecting
      if (inView) start()
      else stop()
    })
    io.observe(host)
    const onVisibility = () => (document.hidden ? stop() : start())
    document.addEventListener('visibilitychange', onVisibility)
    const ro = new ResizeObserver(() => {
      if (configure() && !running) render(time, false)
    })
    ro.observe(host)

    render(0, false)
    reveal()
    start()

    return () => {
      stop()
      io.disconnect()
      ro.disconnect()
      document.removeEventListener('visibilitychange', onVisibility)
      delete host.dataset.ready
      back = null
      front = null
    }
  }, [])

  return (
    <div
      className="about-globe-canvas"
      ref={hostRef}
      role="img"
      aria-label="نمایش مفهومی کرهٔ زمین با ارتباط‌های تجاری شیراز و شهرهای مهم؛ داده زنده نیست."
    >
      <canvas ref={canvasRef} style={{ opacity: 0, transition: 'opacity 0.8s ease' }} />
    </div>
  )
}
