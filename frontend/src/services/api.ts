'use client'

// Acessa localStorage — deve rodar apenas no cliente (browser).
// 'use client' garante que este módulo não seja executado no servidor.

import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor de request: injeta o token JWT no header Authorization
api.interceptors.request.use(
  (config) => {
    // Lê o token armazenado no localStorage após o login
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor de response: ao receber 401, encerra a sessão e redireciona
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Limpa todos os dados de autenticação do localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      // Redireciona para login via window.location (client-side)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
