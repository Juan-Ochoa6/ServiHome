import { useCallback, useEffect, useMemo, useState } from 'react';
import { AuthContext } from './contexto.js';
import {
  EVENTO_SESION_EXPIRADA,
  borrarSesion,
  guardarSesion,
  leerSesion,
} from '../services/api.js';

function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(leerSesion);

  // Si la API no pudo renovar el token, cierra la sesión en pantalla.
  useEffect(() => {
    function alExpirar() {
      setSesion(null);
    }
    window.addEventListener(EVENTO_SESION_EXPIRADA, alExpirar);
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, alExpirar);
  }, []);

  const iniciar = useCallback((respuesta) => {
    const nueva = {
      access: respuesta.access,
      refresh: respuesta.refresh,
      usuario: respuesta.usuario,
      // El backend todavía no devuelve el rol en el login (ver nota al final).
      rol: respuesta.rol ?? null,
    };
    guardarSesion(nueva);
    setSesion(nueva);
  }, []);

  const cerrarSesion = useCallback(() => {
    borrarSesion();
    setSesion(null);
  }, []);

  const valor = useMemo(
    () => ({ sesion, iniciar, cerrarSesion }),
    [sesion, iniciar, cerrarSesion],
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export default AuthProvider;