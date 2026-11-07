import { obtenerPerfil } from '../services/cuenta.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import FormularioPerfil from '../components/FormularioPerfil.jsx';
import PanelVerificacion from '../components/PanelVerificacion.jsx';

function MiCuenta() {
  const { sesion } = useAuth();
  const esProfesional = sesion?.rol === 'profesional';
  const perfil = useCargar(obtenerPerfil);

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">MI CUENTA</span>
        <h2>Mi cuenta</h2>
        <p>
          {esProfesional
            ? 'Administra tus datos, tu verificación y tu disponibilidad.'
            : 'Administra tus datos de contacto.'}
        </p>
      </div>

      <div className="pagina-cuenta">
        <EstadoCarga
          cargando={perfil.cargando && !perfil.datos}
          error={perfil.error}
          onReintentar={perfil.recargar}
          texto="Cargando tu perfil…"
        />

        {perfil.datos && !perfil.error && (
          <FormularioPerfil
            perfil={perfil.datos}
            esProfesional={esProfesional}
            onGuardado={perfil.recargar}
          />
        )}

        {esProfesional && <PanelVerificacion />}
      </div>
    </section>
  );
}

export default MiCuenta;