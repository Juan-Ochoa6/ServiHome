import { useContext } from 'react';
import ConfirmacionContext from './ConfirmacionContext.js';

export function useConfirmacion() {
  const contexto = useContext(ConfirmacionContext);

  if (!contexto) {
    throw new Error(
      'useConfirmacion debe utilizarse dentro de ConfirmacionProvider'
    );
  }

  return contexto.confirmar;
}