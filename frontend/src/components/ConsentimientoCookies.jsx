
import { useState } from 'react';

const CLAVE_CONSENTIMIENTO = 'servihome-consentimiento-cookies';

const preferenciasIniciales = {
  necesarias: true,
  analiticas: false,
};

function ConsentimientoCookies() {
  const [preferencias, setPreferencias] = useState(() => {
    try {
      const guardado = localStorage.getItem(CLAVE_CONSENTIMIENTO);

      if (guardado) {
        const datos = JSON.parse(guardado);

        if (
          typeof datos.necesarias === 'boolean' &&
          typeof datos.analiticas === 'boolean' &&
          datos.necesarias === true
        ) {
          return datos;
        }
      }
    } catch {
      console.warn('No fue posible leer las preferencias de cookies.');
    }

    return preferenciasIniciales;
  });

  const [visible, setVisible] = useState(() => {
    try {
      const guardado = localStorage.getItem(CLAVE_CONSENTIMIENTO);

      if (!guardado) return true;

      const datos = JSON.parse(guardado);

      return !(
        typeof datos.necesarias === 'boolean' &&
        typeof datos.analiticas === 'boolean' &&
        datos.necesarias === true
      );
    } catch {
      return true;
    }
  });

  const [configurando, setConfigurando] = useState(false);

  // Guardar la decisión del usuario.
  function guardarPreferencias(nuevasPreferencias) {
    const consentimiento = {
      ...nuevasPreferencias,
      necesarias: true,
      fecha: new Date().toISOString(),
    };

    try {
      localStorage.setItem(
        CLAVE_CONSENTIMIENTO,
        JSON.stringify(consentimiento)
      );
    } catch {
      console.warn('No fue posible guardar las preferencias de cookies.');
    }

    setPreferencias(consentimiento);
    setVisible(false);
    setConfigurando(false);
  }

  // Aceptar todas las categorías disponibles.
  function aceptarTodas() {
    guardarPreferencias({
      necesarias: true,
      analiticas: true,
    });
  }

  // Rechazar las cookies opcionales.
  function rechazarOpcionales() {
    guardarPreferencias({
      necesarias: true,
      analiticas: false,
    });
  }

  function cambiarPreferencia(nombre, valor) {
    setPreferencias((actuales) => ({
      ...actuales,
      [nombre]: valor,
    }));
  }

  if (!visible) {
    return null;
  }

  return (
    <div
      className="cookies-contenedor"
      role="dialog"
      aria-modal="false"
      aria-labelledby="cookies-titulo"
      aria-describedby="cookies-descripcion"
    >
      <div className="cookies-contenido">
        <div className="cookies-texto">
          <span className="cookies-icono" aria-hidden="true">
            🍪
          </span>

          <div>
            <h2 id="cookies-titulo">
              Tu privacidad nos importa
            </h2>

            <p id="cookies-descripcion">
              En ServiHome utilizamos cookies y tecnologías similares
              para garantizar el funcionamiento de la plataforma.
              Con tu autorización podremos utilizar cookies opcionales
              para mejorar tu experiencia.
            </p>

            <a href="/politica-cookies">
              Conoce nuestra política de cookies
            </a>
          </div>
        </div>

        {configurando && (
          <div className="cookies-preferencias">
            <h3>Configura tus preferencias</h3>

            <div className="cookies-opcion">
              <div>
                <strong>Cookies necesarias</strong>
                <p>
                  Permiten el funcionamiento básico y la seguridad
                  de ServiHome.
                </p>
              </div>

              <input
                type="checkbox"
                checked
                disabled
                aria-label="Cookies necesarias siempre activas"
              />
            </div>

            <div className="cookies-opcion">
              <div>
                <strong>Cookies analíticas</strong>
                <p>
                  Permiten analizar el uso de la plataforma para
                  mejorar sus funcionalidades. Se activarán
                  únicamente cuando exista una herramienta
                  de analítica integrada.
                </p>
              </div>

              <input
                type="checkbox"
                checked={preferencias.analiticas}
                onChange={(evento) =>
                  cambiarPreferencia('analiticas', evento.target.checked)
                }
                aria-label="Permitir cookies analíticas"
              />
            </div>
          </div>
        )}

        <div className="cookies-acciones">
          {configurando ? (
            <>
              <button
                type="button"
                className="cookies-boton cookies-rechazar"
                onClick={rechazarOpcionales}
              >
                Rechazar opcionales
              </button>

              <button
                type="button"
                className="cookies-boton cookies-aceptar"
                onClick={() => guardarPreferencias(preferencias)}
              >
                Guardar preferencias
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="cookies-boton cookies-rechazar"
                onClick={rechazarOpcionales}
              >
                Rechazar opcionales
              </button>

              <button
                type="button"
                className="cookies-boton cookies-configurar"
                onClick={() => setConfigurando(true)}
              >
                Configurar
              </button>

              <button
                type="button"
                className="cookies-boton cookies-aceptar"
                onClick={aceptarTodas}
              >
                Aceptar todas
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConsentimientoCookies;
