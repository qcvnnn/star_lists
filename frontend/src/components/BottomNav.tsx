import { Navbar, Nav } from 'react-bootstrap'
export default function BottomNav({ feed, draft }: { feed: boolean; draft: boolean }) {
 const icons = import.meta.env.BASE_URL + 'icons/'
 return <Navbar className="bottom-nav" aria-label="Основная навигация"><Nav>
  <Nav.Link href="#/feed" active={feed} aria-current={feed ? 'page' : undefined}><img src={icons + 'feed.svg'} alt=""/>Лента</Nav.Link>
  <Nav.Link disabled active={draft} aria-disabled="true"><img src={icons + 'add.svg'} alt=""/>Добавление</Nav.Link>
  <Nav.Link href="#/catalog" active={!feed && !draft} aria-current={!feed && !draft ? 'page' : undefined}><img src={icons + 'grid.svg'} alt=""/>Плитка</Nav.Link>
  <Nav.Link disabled aria-disabled="true"><span aria-hidden="true" className="login-icon">♙</span>Вход</Nav.Link>
 </Nav></Navbar>
}
