function Cargando({ texto = 'Cargando…' }) {
  return (
    <p className="cargando" role="status">
      {texto}
    </p>
  );
}

export default Cargando;