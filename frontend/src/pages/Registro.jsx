import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ErrorApi, registrarUsuario } from '../services/api.js';
import Campo from '../components/Campo.jsx';
import Mensaje from '../components/Mensaje.jsx';

const formularioInicial = {
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  rol: 'cliente',
  telefono: '',
  direccion: '',
};

function Registro() {
  const [datos, setDatos] = useState(formularioInicial);
  const [errores, setErrores] = useState({});
  const [errorGeneral, setErrorGeneral] = useState('');
  const [cargando, setCargando] = useState(false);
  const [rolRegistrado, setRolRegistrado] = useState(null);

  function actualizar(evento) {
    const { name, value } = evento.target;
    setDatos((actual) => ({ ...actual, [name]: value }));
  }

  function mensajeCampo(nombre) {
    const valor = errores[nombre];
    return Array.isArray(valor) ? valor[0] : (valor ?? '');
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErrores({});
    setErrorGeneral('');
    setCargando(true);

    try {
      await registrarUsuario({
        ...datos,
        username: datos.username.trim(),
        email: datos.email.trim(),
      });
      setRolRegistrado(datos.rol);
    } catch (err) {
      if (err instanceof ErrorApi && err.status === 400 && err.datos && typeof err.datos === 'object') {
        setErrores(err.datos);
      } else {
        setErrorGeneral(err.message);
      }
    } finally {
      setCargando(false);
    }
  }

  if (rolRegistrado) {
    return (
      <section className="seccion panel-flujo">
        <div className="formulario-solicitud formulario-auth confirmacion-solicitud">
          <div className="confirmacion-icono" aria-hidden="true">✓</div>
          <span className="etiqueta">CUENTA CREADA</span>
          <h2>¡Registro exitoso!</h2>
          <p>
            {rolRegistrado === 'profesional'
              ? 'Tu perfil quedará pendiente de verificación antes de poder recibir solicitudes.'
              : 'Ya puedes iniciar sesión y solicitar servicios.'}
          </p>
          <Link className="boton-contactar" to="/login">Ir a iniciar sesión</Link>
        </div>
      </section>
    );
  }

  return (
    <section className="seccion panel-flujo">
      <div className="formulario-solicitud formulario-auth">
        <span className="etiqueta">NUEVA CUENTA</span>
        <h2>Crear cuenta</h2>
        <p>Regístrate como cliente o como profesional.</p>

        <form onSubmit={enviar}>
          <Campo id="rol" etiqueta="Quiero…" error={mensajeCampo('rol')}>
            <select id="rol" name="rol" value={datos.rol} onChange={actualizar}>
              <option value="cliente">Contratar servicios (cliente)</option>
              <option value="profesional">Ofrecer servicios (profesional)</option>
            </select>
          </Campo>

          <Campo id="first_name" etiqueta="Nombres" error={mensajeCampo('first_name')}>
            <input
              id="first_name"
              name="first_name"
              type="text"
              autoComplete="given-name"
              value={datos.first_name}
              onChange={actualizar}
              required
            />
          </Campo>

          <Campo id="last_name" etiqueta="Apellidos" error={mensajeCampo('last_name')}>
            <input
              id="last_name"
              name="last_name"
              type="text"
              autoComplete="family-name"
              value={datos.last_name}
              onChange={actualizar}
              required
            />
          </Campo>

          <Campo id="username" etiqueta="Usuario" error={mensajeCampo('username')}>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              value={datos.username}
              onChange={actualizar}
              required
            />
          </Campo>

          <Campo id="email" etiqueta="Correo electrónico" error={mensajeCampo('email')}>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={datos.email}
              onChange={actualizar}
              required
            />
          </Campo>

          <Campo id="password" etiqueta="Contraseña" error={mensajeCampo('password')}>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              value={datos.password}
              onChange={actualizar}
              required
            />
          </Campo>

          <Campo id="telefono" etiqueta="Teléfono (opcional)" error={mensajeCampo('telefono')}>
            <input
              id="telefono"
              name="telefono"
              type="tel"
              autoComplete="tel"
              maxLength={20}
              value={datos.telefono}
              onChange={actualizar}
            />
          </Campo>

          <Campo id="direccion" etiqueta="Dirección (opcional)" error={mensajeCampo('direccion')}>
            <input
              id="direccion"
              name="direccion"
              type="text"
              autoComplete="street-address"
              maxLength={255}
              value={datos.direccion}
              onChange={actualizar}
            />
          </Campo>

          <Mensaje tipo="error">{errorGeneral}</Mensaje>

          <button type="submit" className="boton-contactar" disabled={cargando}>
            {cargando ? 'Creando cuenta…' : 'Crear cuenta'}
          </button>
        </form>

        <p className="enlace-auth">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </div>
    </section>
  );
}

export default Registro;