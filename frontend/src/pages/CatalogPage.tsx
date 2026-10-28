import type { Star } from '../types'
import StarCard from '../components/StarCard'
import DateFilter from '../components/DateFilter'
interface Props {
 stars: Star[]
 date: string
 onDateChange: (date: string) => void
 onApply: () => void
 onReset: () => void
}
export default function CatalogPage({
 stars, date, onDateChange, onApply, onReset
}: Props) {
 return <section className="catalog page">
 <header><h1>Все системы</h1></header>
 <DateFilter
  value={date}
  onChange={onDateChange}
  onApply={onApply}
  onReset={onReset}
 />
 <p className="result-count" aria-live="polite">Найдено: {stars.length}</p>
 <div className="cards">
  {stars.map(star => <StarCard key={star.id} star={star}/>)}
 </div>
 {stars.length === 0 &&
  <p className="empty-state">
   На эту дату звёзд нет. Выберите другую дату или сбросьте фильтр.
  </p>
 }
 </section>
}
