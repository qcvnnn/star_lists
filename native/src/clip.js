import { AutoProcessor, AutoTokenizer, CLIPTextModelWithProjection, CLIPVisionModelWithProjection, RawImage, env } from '@huggingface/transformers'

const modelId = 'Xenova/clip-vit-base-patch32'
export const threshold = 0.64
export const topK = 3
let loading
const textVectors = new Map()
if (typeof window !== 'undefined') env.backends.onnx.wasm.numThreads = 1

function load() {
  loading ??= Promise.all([
    AutoTokenizer.from_pretrained(modelId),
    AutoProcessor.from_pretrained(modelId),
    CLIPTextModelWithProjection.from_pretrained(modelId, { dtype: 'q8' }),
    CLIPVisionModelWithProjection.from_pretrained(modelId, { dtype: 'q8' }),
  ]).catch(error => { loading = undefined; throw error })
  return loading
}

export function similarity(a, b) {
  let product = 0, aa = 0, bb = 0
  for (let i = 0; i < a.length; i++) {
    product += a[i] * b[i]
    aa += a[i] ** 2
    bb += b[i] ** 2
  }
  return aa && bb ? (1 + product / Math.sqrt(aa * bb)) / 2 : 0
}

export async function scoreCards(file, cards) {
  if (!file.type.startsWith('image/')) throw Error('Выберите изображение.')
  if (file.size > 15 * 1024 * 1024) throw Error('Размер изображения не должен превышать 15 МБ.')
  const [tokenizer, processor, textModel, visionModel] = await load()
  const image = await RawImage.fromBlob(file)
  const { image_embeds } = await visionModel(await processor(image))
  const matches = []
  for (const card of cards) {
    let vector = textVectors.get(card.clip_description)
    if (!vector) {
      const { text_embeds } = await textModel(tokenizer(card.clip_description, { truncation: true }))
      vector = text_embeds.data
      textVectors.set(card.clip_description, vector)
    }
    matches.push({ ...card, score: similarity(image_embeds.data, vector) })
  }
  return matches.sort((a, b) => b.score - a.score)
}

export async function findSimilar(file, cards) {
  return (await scoreCards(file, cards))
    .filter(card => card.score >= threshold).slice(0, topK)
}
