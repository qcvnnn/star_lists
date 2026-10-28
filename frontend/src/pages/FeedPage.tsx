import { useEffect, useState } from 'react'
import { Button } from 'react-bootstrap'
import type { Star } from '../types'
import { StarImage, StarVideo } from '../components/Media'
import { formatDate } from '../components/StarCard'
export default function FeedPage({ stars, id }: { stars: Star[]; id?: number }) {
 const [expanded, setExpanded] = useState(false)
 useEffect(() => { setExpanded(false) }, [id])
 const index = id === undefined ? 0 : stars.findIndex(star => star.id === id)
 const star = stars[index]
 if (!star) return <section className="page empty-state"><h1>Звезда не найдена</h1><a href="#/catalog">Вернуться к плитке</a></section>
 const next = stars[(index + 1) % stars.length]
 const icons = import.meta.env.BASE_URL + 'icons/'
 return <article className="feed-page">
  <StarVideo src={star.video_url} poster={star.image_url}/><div className="feed-shade"/>
  
  <div className="feed-overlay"><div className="feed-description"><div className="feed-heading"><StarImage key={star.id} src={star.image_url} title={star.title} className="avatar"/><h1>{star.title}</h1></div>
  <p>{expanded ? star.description : star.description.slice(0, 120) + (star.description.length > 120 ? '…' : '')}</p>
  {star.description.length > 120 && <Button variant="link" className="more-button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Меньше' : 'Больше'}</Button>}
</div>
  <div className="feed-facts"><span title="Дата получения"><img src={icons + 'calendar.svg'} alt="Дата получения"/>{formatDate(star.received_date)}</span><span title="Планеты в зоне обитаемости"><img src={icons + 'planet.svg'} alt="Планеты в зоне обитаемости"/>{star.habitable_planets ?? '—'}</span><span title="Количество лайков">♡ {star.likes_count}</span><Button href={'#/feed/' + next.id} aria-label="Следующая звезда" className="next-button">→</Button></div></div>
 </article>
}
