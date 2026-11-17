import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Footer from './components/footer';
import Nav from './components/nav';

test('shows CraftLab branding', () => {
  render(<MemoryRouter><Footer /></MemoryRouter>);
  expect(screen.getByRole('link', { name: 'CraftLab' })).toBeInTheDocument();
});

test('offers the workshop catalogue to visitors', () => {
  render(<MemoryRouter><Nav loggedIn={false} orders={0} /></MemoryRouter>);
  expect(screen.getByRole('link', { name: 'Мастер-классы' })).toHaveAttribute('href', '/recipes');
  expect(screen.queryByRole('link', { name: 'Список материалов' })).not.toBeInTheDocument();
});

test('offers publishing and materials to signed in makers', () => {
  render(<MemoryRouter><Nav loggedIn orders={2} /></MemoryRouter>);
  expect(screen.getByRole('link', { name: 'Создать мастер-класс' })).toHaveAttribute('href', '/recipes/create');
  expect(screen.getByRole('link', { name: 'Список материалов' })).toHaveAttribute('href', '/cart');
  expect(screen.getByText('2')).toBeInTheDocument();
});
