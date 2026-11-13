import { useContext } from 'react';
import { AuthContext } from './contexto.js';

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error('useAuth debe usarse dentro de <AuthProvider>.');
  }
  return contexto;
}