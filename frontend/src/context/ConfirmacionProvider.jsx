
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';

import ConfirmacionContext from './ConfirmacionContext.js';

export function ConfirmacionProvider({ children }) {
  const [dialogo, setDialogo] = useState(null);
  const resolverRef = useRef(null);

  const resolver = useCallback((resultado) => {
    resolverRef.current?.(resultado);
    resolverRef.current = null;
    setDialogo(null);
  }, []);

  const confirmar = useCallback((opciones = {}) => {
    return new Promise((resolve) => {
      if (resolverRef.current) {
        resolverRef.current(false);
      }

      resolverRef.current = resolve;

      setDialogo({
        titulo: opciones.titulo || '¿Estás seguro?',
        mensaje: opciones.mensaje || '',
        textoConfirmar: opciones.textoConfirmar || 'Confirmar',
        textoCancelar: opciones.textoCancelar || 'Cancelar',
        tipo: opciones.tipo || 'info'
      });
    });
  }, []);

  useEffect(() => {
    if (!dialogo) return;

    const manejarTecla = (evento) => {
      if (evento.key === 'Escape') {
        resolver(false);
      }
    };

    window.addEventListener('keydown', manejarTecla);

    return () => {
      window.removeEventListener('keydown', manejarTecla);
    };
  }, [dialogo, resolver]);

  const valor = useMemo(() => ({ confirmar }), [confirmar]);

  return (
    <ConfirmacionContext.Provider value={valor}>
      {children}

      {dialogo && (
        <div className="confirmacion-overlay">
          <section
            className={`confirmacion-dialogo tipo-${dialogo.tipo}`}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirmacion-titulo"
            aria-describedby="confirmacion-mensaje"
          >
            <div className="confirmacion-icono">
              {dialogo.tipo === 'peligro' ? '!' : '?'}
            </div>

            <h2 id="confirmacion-titulo">
              {dialogo.titulo}
            </h2>

            <p id="confirmacion-mensaje">
              {dialogo.mensaje}
            </p>

            <div className="confirmacion-acciones">
              <button
                type="button"
                className="confirmacion-boton cancelar"
                onClick={() => resolver(false)}
              >
                {dialogo.textoCancelar}
              </button>

              <button
                type="button"
                className="confirmacion-boton aceptar"
                onClick={() => resolver(true)}
                autoFocus
              >
                {dialogo.textoConfirmar}
              </button>
            </div>
          </section>
        </div>
      )}
    </ConfirmacionContext.Provider>
  );
}
