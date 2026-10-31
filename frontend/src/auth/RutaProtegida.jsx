import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth.js';

// roles es opcional: <RutaProtegida roles={['profesional']}>
// Mientras el backend no devuelva el rol, solo se exige estar autenticado.
function RutaProtegida({ children, roles }) {
  const { sesion } = useAuth();
  const location = useLocation();

  if (!sesion) {
    return <Navigate to="/login" replace state={{ desde: location }} />;
  }

  if (roles && sesion.rol && !roles.includes(sesion.rol)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default RutaProtegida;