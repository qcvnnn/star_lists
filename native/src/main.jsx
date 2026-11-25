import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { invoke } from '@tauri-apps/api/core'
import './styles.css'

const fallback = new URL('./default-star.jpg', window.location.href).href
function imageUrl(value, host) {
  if (!value) return fallback
  try {
    const url = new URL(value, 'http://' + host + ':8000')
    if (['localhost', '127.0.0.1', '0.0.0.0'].includes(url.hostname)) url.hostname = host
    return ['http:', 'https:'].includes(url.protocol) ? url.href : fallback
  } catch { return fallback }
}

function App() {
  const [host, setHost] = useState(localStorage.getItem('server-ip') || import.meta.env.VITE_SERVER_IP || '172.16.242.254')
  const [activeHost, setActiveHost] = useState(host)
  const [cards, setCards] = useState([])
  const [name, setName] = useState('')
  const [date, setDate] = useState('')
  const [selected, setSelected] = useState(null)
  const [results, setResults] = useState(null)
  const [network, setNetwork] = useState('')
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')
  const loadVersion = useRef(0)
  const lookupVersion = useRef(0)

  async function refresh(server) {
    const version = ++loadVersion.current
    lookupVersion.current++
    setSearching(false)
    setResults(null)
    setNetwork('Загружаем каталог…')
    try {
      const data = await invoke('load_catalog', { host: server })
      if (version !== loadVersion.current) return
      setCards(data)
      setActiveHost(server)
      localStorage.setItem('server-ip', server)
      setNetwork('')
    } catch (err) {
      if (version === loadVersion.current) setNetwork(String(err))
    }
  }

  useEffect(() => { void refresh(host) }, [])

  async function search(file) {
    if (!file) return
    const version = ++lookupVersion.current
    setSearching(true)
    setError('')
    setResults(null)
    try {
      const { findSimilar } = await import('./clip.js')
      const visible = cards.filter(matchesFilters)
      const found = await findSimilar(file, visible)
      if (version === lookupVersion.current) setResults(found)
    } catch (err) {
      if (version === lookupVersion.current) setError(String(err))
    } finally {
      if (version === lookupVersion.current) setSearching(false)
    }
  }

  function matchesFilters(card) {
    return card.title.toLocaleLowerCase('ru').includes(name.trim().toLocaleLowerCase('ru'))
      && (!date || card.received_date === date)
  }

  function resetSearch() {
    lookupVersion.current++
    setResults(null)
    setSearching(false)
    setError('')
  }

  const card = cards.find(item => item.id === selected)
  const filtered = (results ?? cards).filter(matchesFilters)
  const image = item => <img src={imageUrl(item.image_url, activeHost)} alt={item.title}
    onError={event => { if (event.currentTarget.src !== fallback) event.currentTarget.src = fallback }} />

  return <main>
    <header><h1>Звёздные системы</h1>
      <form onSubmit={event => { event.preventDefault(); void refresh(host.trim()) }}>
        <label>IP сервера <input value={host} onChange={event => setHost(event.target.value)} required /></label>
        <button>Обновить каталог</button>
      </form>
      {network && <p role="status">{network}</p>}
    </header>
    {card ? <section className="details">
      <button onClick={() => setSelected(null)}>← К каталогу</button>
      {image(card)}
      <h2>{card.title}</h2>
      <p>{card.description || 'Описание пока не добавлено.'}</p>
      <p>Дата получения: {card.received_date || '—'}</p>
      <p>Планет в зоне обитаемости: {card.habitable_planets ?? '—'}</p>
    </section> : <>
      <section className="filters">
        <label>Название <input value={name} onChange={event => { setName(event.target.value); resetSearch() }} /></label>
        <label>Дата получения <input type="date" value={date} onChange={event => { setDate(event.target.value); resetSearch() }} /></label>
        <label>Поиск по изображению <input type="file" accept="image/*" disabled={!cards.length || searching}
          onChange={event => { void search(event.target.files[0]); event.target.value = '' }} /></label>
        {(results || searching || error) && <button onClick={resetSearch}>Сбросить поиск по фото</button>}
      </section>
      {searching && <p role="status">Сравниваем изображение с описаниями. При первом запуске загружается модель CLIP.</p>}
      {error && <p role="alert">{error}</p>}
      {!searching && !filtered.length && <p>Карточки не найдены</p>}
      <section className="catalog">{filtered.map(item => <article key={item.id}>
        {image(item)}<h2>{item.title}</h2>
        {item.score !== undefined && <p>Сходство: {item.score.toFixed(3)}</p>}
        <button onClick={() => setSelected(item.id)}>Подробнее</button>
      </article>)}</section>
    </>}
  </main>
}

createRoot(document.getElementById('root')).render(<App />)
