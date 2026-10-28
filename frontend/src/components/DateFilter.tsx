import { Button, Form } from 'react-bootstrap'

interface Props {
  value: string
  onChange: (value: string) => void
  onApply: () => void
  onReset: () => void
}

export default function DateFilter({ value, onChange, onApply, onReset }: Props) {
  return (
    <Form className="date-filter" onSubmit={event => {
      event.preventDefault()
      onApply()
    }}>
      <Form.Group controlId="received-date">
        <Form.Label>Дата получения</Form.Label>
        <Form.Control
          type="text" inputMode="numeric"
          placeholder="дд.мм.гггг" maxLength={10}
          pattern="[0-9]{2}\.[0-9]{2}\.[0-9]{4}"
          title="Дата в формате дд.мм.гггг"
          value={value}
          onChange={event => onChange(event.target.value)}
        />
      </Form.Group>
      <Button type="submit">Найти</Button>
      <Button variant="outline-light" type="button" onClick={onReset}>
        Сбросить
      </Button>
    </Form>
  )
}
