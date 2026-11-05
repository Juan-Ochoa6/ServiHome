import { useCallback, useEffect, useMemo, useState } from 'react';
import { AuthContext } from './contexto.js';
import {
  EVENTO_SESION_EXPIRADA,
  borrarSesion,
  guardarSesion,
  leerSesion,
} from '../services/api.js';

function AuthProvider({ children }) {
  // Una sesión guardada sin rol es de una versión anterior: se ignora
  // y el usuario vuelve a iniciar sesión.
  const [sesion, setSesion] = useState(() => {
    const guardada = leerSesion();
    return guardada?.rol ? guardada : null;
  });

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
<<<<<<< HEAD
      rol: respuesta.rol ?? null, // cliente | profesional | administrador
=======
      // Guardar el rol recibido desde Django.
      rol: respuesta.rol ?? null,
>>>>>>> 5b1dbd1 (Implementa mejoras de usuarios y servicios)
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