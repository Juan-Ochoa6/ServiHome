
import { obtenerEstadisticasGenerales } from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import EstadoCarga from './EstadoCarga.jsx';

function humanizarEstado(estado) {
    return estado
        .replaceAll('_', ' ')
        .replace(/\b\w/g, (letra) => letra.toUpperCase());
}

function GraficaBarras({ titulo, elementos, nombreCampo }) {
    const maximo = Math.max(1, ...elementos.map((elemento) => elemento.cantidad));

    return (
        <section className="tarjeta-panel tarjeta-estadistica">
            <h3 className="titulo-tablero">{titulo}</h3>

            {elementos.length === 0 ? (
                <p className="sin-resultados">No hay datos disponibles.</p>
            ) : (
                <div className="grafica-barras">
                    {elementos.map((elemento) => {
                        const ancho = (elemento.cantidad / maximo) * 100;

                        return (
                            <div className="barra-item" key={elemento[nombreCampo]}>
                                <div className="barra-info">
                                    <span>{humanizarEstado(elemento[nombreCampo])}</span>
                                    <strong>{elemento.cantidad}</strong>
                                </div>

                                <div
                                    className="barra-fondo"
                                    role="progressbar"
                                    aria-label={`${humanizarEstado(elemento[nombreCampo])}: ${elemento.cantidad}`}
                                    aria-valuenow={elemento.cantidad}
                                    aria-valuemin={0}
                                    aria-valuemax={maximo}
                                >
                                    <span style={{ width: `${ancho}%` }} />
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

function GraficaProfesionales({ elementos }) {
    const total = elementos.reduce(
        (suma, elemento) => suma + elemento.cantidad,
        0
    );

    const colores = ['#23865b', '#e0a13b', '#4389bd', '#c66b6b', '#8b78b5'];

    const segmentos = elementos.map((elemento, indice) => {
        const cantidadAnterior = elementos
            .slice(0, indice)
            .reduce((suma, item) => suma + item.cantidad, 0);

        const inicio = total > 0 ? (cantidadAnterior / total) * 100 : 0;
        const fin = total > 0
            ? ((cantidadAnterior + elemento.cantidad) / total) * 100
            : 0;

        return {
            ...elemento,
            color: colores[indice % colores.length],
            inicio,
            fin,
        };
    });

    const gradiente = total > 0
        ? `conic-gradient(${segmentos
            .map((segmento) => `${segmento.color} ${segmento.inicio}% ${segmento.fin}%`)
            .join(', ')})`
        : '#e3ebe5';

    return (
        <section className="tarjeta-panel tarjeta-estadistica">
            <h3 className="titulo-tablero">Profesionales por verificación</h3>

            {total === 0 ? (
                <p className="sin-resultados">Todavía no hay profesionales registrados.</p>
            ) : (
                <div className="grafica-circular-contenido">
                    <div
                        className="grafica-circular"
                        style={{ background: gradiente }}
                        role="img"
                        aria-label={`Distribución de ${total} profesionales por estado de verificación`}
                    >
                        <div>
                            <strong>{total}</strong>
                            <span>Profesionales</span>
                        </div>
                    </div>

                    <ul className="leyenda-grafica">
                        {segmentos.map((segmento) => (
                            <li key={segmento.estado}>
                                <span
                                    className="leyenda-color"
                                    style={{ background: segmento.color }}
                                />
                                <span>{humanizarEstado(segmento.estado)}</span>
                                <strong>{segmento.cantidad}</strong>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </section>
    );
}

function GraficaServicios({ elementos }) {
    const maximo = Math.max(1, ...elementos.map((elemento) => elemento.cantidad));

    return (
        <section className="tarjeta-panel tarjeta-estadistica">
            <h3 className="titulo-tablero">Los 5 servicios más solicitados</h3>

            {elementos.length === 0 ? (
                <p className="sin-resultados">Todavía no hay solicitudes registradas.</p>
            ) : (
                <div className="grafica-barras">
                    {elementos.map((elemento, indice) => {
                        const ancho = (elemento.cantidad / maximo) * 100;

                        return (
                            <div className="barra-item" key={elemento.servicio__nombre}>
                                <div className="barra-info">
                                    <span>{indice + 1}. {elemento.servicio__nombre}</span>
                                    <strong>{elemento.cantidad}</strong>
                                </div>

                                <div
                                    className="barra-fondo"
                                    role="progressbar"
                                    aria-label={`${elemento.servicio__nombre}: ${elemento.cantidad}`}
                                    aria-valuenow={elemento.cantidad}
                                    aria-valuemin={0}
                                    aria-valuemax={maximo}
                                >
                                    <span style={{ width: `${ancho}%` }} />
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </section>
    );
}

function PanelEstadisticas() {
    const estadisticas = useCargar(obtenerEstadisticasGenerales);
    const datos = estadisticas.datos;

    return (
        <>
            <p className="nota-panel">
                Información general y agregada de la actividad de ServiHome.
            </p>

            <EstadoCarga
                cargando={estadisticas.cargando && !datos}
                error={estadisticas.error}
                onReintentar={estadisticas.recargar}
                texto="Cargando estadísticas..."
            />

            {datos && !estadisticas.error && (
                <>
                    <div className="tablero">
                        <div className="dato-tablero">
                            <span>Servicios completados</span>
                            <strong>{datos.servicios_completados}</strong>
                            <span>Solicitudes finalizadas</span>
                        </div>

                        <div className="dato-tablero">
                            <span>Servicios en el ranking</span>
                            <strong>{datos.servicios_mas_solicitados.length}</strong>
                            <span>Entre los más solicitados</span>
                        </div>
                    </div>

                    <div className="estadisticas-grid">
                        <GraficaBarras
                            titulo="Solicitudes por estado"
                            elementos={datos.solicitudes_por_estado}
                            nombreCampo="estado"
                        />

                        <GraficaProfesionales
                            elementos={datos.profesionales_por_verificacion}
                        />

                        <GraficaBarras
                            titulo="Ofertas por estado de aprobación"
                            elementos={datos.ofertas_por_estado}
                            nombreCampo="estado"
                        />

                        <GraficaServicios
                            elementos={datos.servicios_mas_solicitados}
                        />
                    </div>
                </>
            )}
        </>
    );
}

export default PanelEstadisticas;
