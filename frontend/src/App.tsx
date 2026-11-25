import { useEffect, useState } from 'react'
import { useRef } from 'react'
import { starsMock } from './data/stars'
import BottomNav from './components/BottomNav'
import CatalogPage from './pages/CatalogPage'
import FeedPage from './pages/FeedPage'
import AddPage from './pages/AddPage'
import type { Star } from './types'

const api = '/api/star_list'
const live = import.meta.env.DEV || import.meta.env.VITE_LIVE_API === 'true'
const limit = 10

interface CatalogResult {
 data: Star[]
 total: number
}

async function getJson<T>(path: string, signal: AbortSignal): Promise<T> {
 const response = await fetch(api + path, { signal })
 if (!response.ok) throw new Error(`HTTP ${response.status}`)
 return response.json()
}

export default function App() {
 const [route, setRoute] = useState(window.location.hash.slice(1) || '/catalog')
 const [date, setDate] = useState('')
 const [appliedDate, setAppliedDate] = useState('')
 const [page, setPage] = useState(1)
 const [catalog, setCatalog] = useState<CatalogResult>()
 const [feed, setFeed] = useState<Star>()
 const [error, setError] = useState('')
 const [loading, setLoading] = useState(false)
 const initialFeed = useRef<Promise<unknown> | undefined>(undefined)
 useEffect(() => {
  function onHashChange() {
   setRoute(window.location.hash.slice(1) || '/catalog')
  }
  window.addEventListener('hashchange', onHashChange)
  return () => window.removeEventListener('hashchange', onHashChange)
 }, [])
 const [path, search] = route.split('?')
 const match = path.match(/^\/(feed|stars)(?:\/(\d+))?$/)
 const isFeed = match?.[1] === 'feed'
 const id = match?.[2] ? Number(match[2]) : undefined
 useEffect(() => {
  if (!live) return
  initialFeed.current ??= getJson('/feed', AbortSignal.timeout(10000)).catch(() => {})
 }, [])
 useEffect(() => {
  if (!live || (route !== '/catalog' && !isFeed)) return
  const controller = new AbortController()
  const { signal } = controller
  setLoading(true)
  setError('')
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  if (appliedDate) params.set('received_date', appliedDate)
  const feedParams = new URLSearchParams(search)
  if (id !== undefined) feedParams.set('id', String(id))
  const request = isFeed
   ? Promise.resolve(initialFeed.current).then(() => {
      signal.throwIfAborted()
      return getJson<Star>('/feed?' + feedParams, signal)
     }).then(star => {
      if (!signal.aborted) setFeed({ ...star, description: star.description ?? '' })
     })
   : getJson<CatalogResult>('/catalog?' + params, signal).then(result => {
      if (!signal.aborted) setCatalog(result)
     })
  void request.catch((err: Error) => {
   if (!signal.aborted) setError(err.message)
  }).finally(() => {
   if (!signal.aborted) setLoading(false)
  })
  return () => controller.abort()
 }, [route, isFeed, id, search, appliedDate, page])
 useEffect(() => {
  document.title = (
   isFeed ? 'Лента'
   : route === '/draft' ? 'Добавление' : 'Звёздные системы') + ' — Star List' }, [route, isFeed])
 const filtered = starsMock.filter(star =>
  !appliedDate || star.received_date === appliedDate
 )
 return <div className="app-shell">
 <main className="app-content" key={isFeed ? 'feed' : route}>
 {live && (route === '/catalog' || isFeed) && error ? <p className="page" role="alert">Не удалось загрузить данные ({error}).</p>
 : route === '/catalog' ? <CatalogPage
  stars={live ? catalog?.data ?? [] : filtered}
  page={page}
  total={live ? catalog?.total ?? 0 : filtered.length}
  limit={limit}
  loading={live && (loading || !catalog)}
  onPageChange={setPage}
  date={date}
  onDateChange={setDate}
  onApply={() => {
   setPage(1)
   setAppliedDate(date.split('.').reverse().join('-'))
  }}
  onReset={() => {
   setDate('')
   setAppliedDate('')
   setPage(1)
  }}
 />
 : isFeed ? live
  ? feed && !loading ? <FeedPage key={feed.id} stars={[feed]} id={feed.id} nextHref={`#/feed/${feed.id}?next=true&step=${(Number(new URLSearchParams(search).get('step')) || 0) + 1}`}/>
    : <p className="page" role="status">Загружаем ленту…</p>
  : <FeedPage stars={starsMock} id={id}/>

   : route === '/draft' ? <AddPage/>
 : <section className="page">
  <h1>Страница не найдена</h1>
  <a href="#/catalog">К плитке</a>
 </section>}
 </main>
 <BottomNav feed={isFeed} draft={route === '/draft'}/>
 </div>
}
