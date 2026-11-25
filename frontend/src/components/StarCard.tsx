import { Card } from 'react-bootstrap'
import type { Star } from '../types'
import { StarImage } from './Media'
export const formatDate = (date: string | null) => date ? date.split('-').reverse().join('.') : '—'
export default function StarCard({ star }: { star: Star }) {
 return <Card className="star-card"><a href={'#/feed/' + star.id} aria-label={'Открыть в ленте ' + star.title}>
 <StarImage src={star.image_url} title={star.title} className="card-cover"/>
 <Card.Body><Card.Title as="h2">{star.title}</Card.Title><p>{formatDate(star.received_date)}</p><div className="card-footer-info"><span>Планет: {star.habitable_planets ?? '—'}</span><span>♡ {star.likes_count}</span></div></Card.Body>
 </a></Card>
}
