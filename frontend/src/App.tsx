import { useEffect, useState } from 'react'
import { starsMock } from './data/stars'
import BottomNav from './components/BottomNav'
import CatalogPage from './pages/CatalogPage'
import FeedPage from './pages/FeedPage'
import AddPage from './pages/AddPage'
export default function App() {
 const [route, setRoute] = useState(window.location.hash.slice(1) || '/catalog')
 const [date, setDate] = useState('')
 const [appliedDate, setAppliedDate] = useState('')
 useEffect(() => {
  function onHashChange() {
   setRoute(window.location.hash.slice(1) || '/catalog')
  }
  window.addEventListener('hashchange', onHashChange)
  return () => window.removeEventListener('hashchange', onHashChange)
 }, [])
 const match = route.match(/^\/(feed|stars)(?:\/(\d+))?$/)
 const isFeed = match?.[1] === 'feed'
 const id = match?.[2] ? Number(match[2]) : undefined
 useEffect(() => {
  document.title = (
   isFeed ? 'Лента'
   : route === '/draft' ? 'Добавление' : 'Звёздные системы') + ' — Star List' }, [route, isFeed])
 const filtered = starsMock.filter(star =>
  !appliedDate || star.received_date === appliedDate
 )
 return <div className="app-shell">
 <main className="app-content" key={isFeed ? 'feed' : route}>
 {route === '/catalog' ? <CatalogPage
  stars={filtered}
  date={date}
  onDateChange={setDate}
  onApply={() =>
   setAppliedDate(date.split('.').reverse().join('-'))
  }
  onReset={() => {
   setDate('')
   setAppliedDate('')
  }}
 />
 : isFeed ? <FeedPage stars={starsMock} id={id}/>

   : route === '/draft' ? <AddPage/>
 : <section className="page">
  <h1>Страница не найдена</h1>
  <a href="#/catalog">К плитке</a>
 </section>}
 </main>
 <BottomNav feed={isFeed} draft={route === '/draft'}/>
 </div>
}
