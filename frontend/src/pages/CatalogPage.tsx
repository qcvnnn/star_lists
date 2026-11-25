import type { Star } from '../types'
import StarCard from '../components/StarCard'
import DateFilter from '../components/DateFilter'
import { Pagination } from 'react-bootstrap'
interface Props {
 stars: Star[]
 page: number
 total: number
 limit: number
 loading: boolean
 onPageChange: (page: number) => void
 date: string
 onDateChange: (date: string) => void
 onApply: () => void
 onReset: () => void
}
export default function CatalogPage({
 stars, date, onDateChange, onApply, onReset, page, total, limit, loading, onPageChange
}: Props) {
 const totalPages = Math.ceil(total / limit)
 return <section className="catalog page">
 <header><h1>Все системы</h1></header>
 <DateFilter
  value={date}
  onChange={onDateChange}
  onApply={onApply}
  onReset={onReset}
 />
 <p className="result-count" aria-live="polite">{loading ? 'Загружаем…' : `Найдено: ${total}`}</p>
 <div className="cards">
  {stars.map(star => <StarCard key={star.id} star={star}/>)}
 </div>
 {totalPages > 1 && <nav aria-label="Страницы каталога" className="mt-3">
  <p>Страница {page} из {totalPages}</p>
  <Pagination size="sm">
   <Pagination.First disabled={loading || page === 1} onClick={() => onPageChange(1)}/>
   <Pagination.Prev disabled={loading || page === 1} onClick={() => onPageChange(page - 1)}/>
   <Pagination.Next disabled={loading || page >= totalPages} onClick={() => onPageChange(page + 1)}/>
   <Pagination.Last disabled={loading || page >= totalPages} onClick={() => onPageChange(totalPages)}/>
  </Pagination>
 </nav>}
 {!loading && stars.length === 0 &&
  <p className="empty-state">
   На эту дату звёзд нет. Выберите другую дату или сбросьте фильтр.
  </p>
 }
 </section>
}
