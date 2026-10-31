import { useCallback, useEffect, useState } from 'react';

// Carga datos de una función de la API.
// "funcion" debe ser estable (una función definida a nivel de módulo).
export function useCargar(funcion) {
  const [estado, setEstado] = useState({ datos: null, error: '', cargando: true });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelado = false;

    funcion()
      .then((datos) => {
        if (!cancelado) setEstado({ datos, error: '', cargando: false });
      })
      .catch((err) => {
        if (!cancelado) setEstado({ datos: null, error: err.message, cargando: false });
      });

    return () => {
      cancelado = true;
    };
  }, [funcion, version]);

  const recargar = useCallback(() => {
    setEstado((actual) => ({ ...actual, cargando: true, error: '' }));
    setVersion((actual) => actual + 1);
  }, []);

  return { ...estado, recargar };
}