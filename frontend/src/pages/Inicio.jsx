import { useAuth } from '../auth/useAuth.js';
import InicioAdmin from '../components/InicioAdmin.jsx';
import InicioCliente from '../components/InicioCliente.jsx';
import InicioProfesional from '../components/InicioProfesional.jsx';
import InicioFinanzas from '../components/InicioFinanzas.jsx';

// Cada rol tiene su propia pantalla de inicio.
function Inicio() {
  const { sesion } = useAuth();

  if (sesion?.rol === 'profesional') return <InicioProfesional />;
  if (sesion?.rol === 'administrador') return <InicioAdmin />;
  if (sesion?.rol === 'finanzas') return <InicioFinanzas />;
  return <InicioCliente />;
}

export default Inicio;