function Mensaje({ tipo = 'error', children }) {
  if (!children) return null;

  return (
    <p
      className={`mensaje mensaje-${tipo}`}
      role={tipo === 'error' ? 'alert' : 'status'}
    >
      {children}
    </p>
  );
}

export default Mensaje;