import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth.js';

// roles: roles que pueden entrar. visitante: deja pasar también a quien no inició sesión.
function RutaProtegida({ children, roles, visitante = false }) {
  const { sesion } = useAuth();
  const location = useLocation();

  if (!sesion) {
    if (visitante) return children;
    return <Navigate to="/login" replace state={{ desde: location }} />;
  }

  if (roles && !roles.includes(sesion.rol)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default RutaProtegida;