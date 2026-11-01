import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { ErrorApi, iniciarSesion, verificarCodigoLogin } from '../services/api.js';
import { useAuth } from '../auth/useAuth.js';
import Campo from '../components/Campo.jsx';
import Mensaje from '../components/Mensaje.jsx';

function Login() {
  const { sesion, iniciar } = useAuth();
  const location = useLocation();
  const destino = location.state?.desde?.pathname ?? '/';

  const [credenciales, setCredenciales] = useState({ username: '', password: '' });
  const [desafio, setDesafio] = useState(null); // { challenge, qr }
  const [codigo, setCodigo] = useState('');
  const [codigosRecuperacion, setCodigosRecuperacion] = useState(null);
  const [copiado, setCopiado] = useState(false);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  // Si ya hay sesión, no se muestra el login (salvo los códigos de recuperación).
  if (sesion && !codigosRecuperacion) {
    return <Navigate to={destino} replace />;
  }

  function actualizarCredenciales(evento) {
    const { name, value } = evento.target;
    setCredenciales((actual) => ({ ...actual, [name]: value }));
  }

  async function enviarCredenciales(evento) {
    evento.preventDefault();
    setError('');
    setCargando(true);

    try {
      const respuesta = await iniciarSesion(
        credenciales.username.trim(),
        credenciales.password,
      );
      setDesafio({
        challenge: respuesta.challenge,
        qr: respuesta.mfa_setup_required ? respuesta.codigo_qr : null,
      });
      setCodigo('');
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  async function enviarCodigo(evento) {
    evento.preventDefault();
    setError('');
    setCargando(true);

    try {
      const respuesta = await verificarCodigoLogin(desafio.challenge, codigo.trim());
      if (respuesta.codigos_recuperacion) {
        setCodigosRecuperacion(respuesta.codigos_recuperacion);
      }
      iniciar(respuesta);
    } catch (err) {
      if (err instanceof ErrorApi && err.status === 401) {
        // Desafío vencido, usado o bloqueado: hay que empezar de nuevo.
        setDesafio(null);
        setCodigo('');
        setError(`${err.message} Inicia sesión de nuevo.`);
      } else if (err instanceof ErrorApi && err.datos?.intentos_restantes !== undefined) {
        setError(`${err.message} Intentos restantes: ${err.datos.intentos_restantes}.`);
      } else {
        setError(err.message);
      }
    } finally {
      setCargando(false);
    }
  }

  function volverACredenciales() {
    setDesafio(null);
    setCodigo('');
    setError('');
  }

  function copiarCodigos() {
    navigator.clipboard
      ?.writeText(codigosRecuperacion.join('\n'))
      .then(() => setCopiado(true))
      .catch(() => setCopiado(false));
  }

  // ----- Pantalla: códigos de recuperación (solo la primera vez) -----
  if (codigosRecuperacion) {
    return (
      <section className="seccion panel-flujo">
        <div className="formulario-solicitud formulario-auth">
          <span className="etiqueta">AUTENTICACIÓN ACTIVADA</span>
          <h2>Guarda tus códigos de recuperación</h2>
          <p>
            Cada código sirve una sola vez para entrar si pierdes acceso a tu
            aplicación autenticadora. No volverán a mostrarse.
          </p>

          <ul className="codigos-recuperacion">
            {codigosRecuperacion.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <div className="acciones-confirmacion">
            <button type="button" className="boton-secundario" onClick={copiarCodigos}>
              {copiado ? 'Copiados ✓' : 'Copiar códigos'}
            </button>
            <button
              type="button"
              className="boton-contactar"
              onClick={() => setCodigosRecuperacion(null)}
            >
              Ya los guardé, continuar
            </button>
          </div>
        </div>
      </section>
    );
  }

  // ----- Pantalla: código MFA -----
  if (desafio) {
    return (
      <section className="seccion panel-flujo">
        <div className="formulario-solicitud formulario-auth">
          <span className="etiqueta">VERIFICACIÓN EN DOS PASOS</span>
          <h2>{desafio.qr ? 'Configura tu autenticador' : 'Ingresa tu código'}</h2>

          {desafio.qr ? (
            <>
              <p>1. Abre Microsoft Authenticator y escanea este código QR.</p>
              <img
                className="qr"
                src={desafio.qr}
                alt="Código QR para configurar Microsoft Authenticator"
              />
              <p>2. Escribe el código de 6 dígitos que aparece en la aplicación.</p>
            </>
          ) : (
            <p>
              Escribe el código de 6 dígitos de Microsoft Authenticator o uno de tus
              códigos de recuperación.
            </p>
          )}

          <form onSubmit={enviarCodigo}>
            <Campo id="codigo" etiqueta="Código">
              <input
                id="codigo"
                name="codigo"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={32}
                value={codigo}
                onChange={(evento) => setCodigo(evento.target.value)}
                required
              />
            </Campo>

            <Mensaje tipo="error">{error}</Mensaje>

            <button type="submit" className="boton-contactar" disabled={cargando}>
              {cargando ? 'Verificando…' : 'Verificar'}
            </button>
            <button type="button" className="boton-secundario" onClick={volverACredenciales}>
              ← Volver
            </button>
          </form>
        </div>
      </section>
    );
  }

  // ----- Pantalla: usuario y contraseña -----
  return (
    <section className="seccion panel-flujo">
      <div className="formulario-solicitud formulario-auth">
        <span className="etiqueta">BIENVENIDO</span>
        <h2>Iniciar sesión</h2>
        <p>Ingresa con tu cuenta de ServiHome.</p>

        <form onSubmit={enviarCredenciales}>
          <Campo id="username" etiqueta="Usuario">
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              value={credenciales.username}
              onChange={actualizarCredenciales}
              required
            />
          </Campo>

          <Campo id="password" etiqueta="Contraseña">
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={credenciales.password}
              onChange={actualizarCredenciales}
              required
            />
          </Campo>

          <Mensaje tipo="error">{error}</Mensaje>

          <button type="submit" className="boton-contactar" disabled={cargando}>
            {cargando ? 'Ingresando…' : 'Continuar'}
          </button>
        </form>

        <p className="enlace-auth">
          ¿No tienes cuenta? <Link to="/registro">Regístrate</Link>
        </p>
      </div>
    </section>
  );
}

export default Login;