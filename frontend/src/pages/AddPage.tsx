import { Form, Button } from 'react-bootstrap'
import { draftMock } from '../data/draft'
import { StarImage, StarVideo } from '../components/Media'
export default function AddPage() {
 return <section className="page draft-page"><h1>Черновик</h1>
 <Form onSubmit={event => event.preventDefault()}>
 <fieldset disabled>
 <div className="uploads">
 <label className="upload"><StarImage src={draftMock.image_url} title="Изображение черновика"/><span>Загрузить фото</span><input type="file" accept="image/*" aria-label="Загрузить фото"/></label>
 <label className="upload"><StarVideo src={draftMock.video_url} poster={draftMock.image_url}/><span>Загрузить видео</span><input type="file" accept="video/*" aria-label="Загрузить видео"/></label>
 </div>
 <Form.Group controlId="star-name"><Form.Label>Название звезды</Form.Label><Form.Control value={draftMock.title} readOnly/></Form.Group>
 <Form.Group controlId="description"><Form.Label>Текстовое описание</Form.Label><Form.Control as="textarea" rows={2} value={draftMock.description} readOnly/></Form.Group>
 <Form.Group controlId="draft-date"><Form.Label>Дата получения</Form.Label><Form.Control type="text" placeholder="??.??.????" value={draftMock.received_date?.split('-').reverse().join('.') ?? ''} readOnly/></Form.Group>
 <Form.Group controlId="planet-count"><Form.Label>Количество планет в зоне обитаемости</Form.Label><Form.Control type="number" min={0} value={draftMock.habitable_planets ?? ''} readOnly/></Form.Group>
 <Button type="submit">Опубликовать</Button>
 </fieldset></Form></section>
}
