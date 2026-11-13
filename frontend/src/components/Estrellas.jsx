function Estrellas({ valor }) {
  const llenas = Math.max(0, Math.min(5, Math.round(Number(valor) || 0)));

  return (
    <span className="estrellas" role="img" aria-label={`${llenas} de 5 estrellas`}>
      {'★'.repeat(llenas)}
      {'☆'.repeat(5 - llenas)}
    </span>
  );
}

export default Estrellas;