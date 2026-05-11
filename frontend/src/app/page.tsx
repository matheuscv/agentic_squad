import { redirect } from 'next/navigation'

// Server Component — redireciona a raiz para /login
export default function Home() {
  redirect('/login')
}
