function Campo({ id, etiqueta, error, children }) {
  return (
    <div className="campo-formulario">
      <label htmlFor={id}>{etiqueta}</label>
      {children}
      {error && (
        <span className="error-campo" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default Campo;