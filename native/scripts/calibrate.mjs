import { env } from '@huggingface/transformers'
import { scoreCards, threshold, topK } from '../src/clip.js'

const host = process.argv[2] ?? '172.16.242.254'
const origin = `http://${host}:8000`
env.cacheDir = './.model-cache'

async function get(url) {
  const response = await fetch(url, { signal: AbortSignal.timeout(15000) })
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`)
  return response
}

const cards = await (await get(new URL('/api/star_list/native/catalog', origin))).json()
for (const card of cards) {
  const url = new URL(card.image_url, origin)
  if (['localhost', '127.0.0.1'].includes(url.hostname)) url.hostname = host
  const scores = await scoreCards(await (await get(url)).blob(), cards)
  const shown = scores.filter(item => item.score >= threshold).slice(0, topK)
  console.log(card.title, '→', shown.map(item => `${item.title} (${item.score.toFixed(4)})`).join(', '))
}
