
import { useSearchParams } from 'react-router-dom';
import PanelFinanzas from '../components/PanelFinanzas.jsx';
import PanelEstadisticas from '../components/PanelEstadisticas.jsx';

function Finanzas() {
    const [parametros, setParametros] = useSearchParams();
    const pestana = parametros.get('pestana') === 'estadisticas'
        ? 'estadisticas'
        : 'finanzas';

    function cambiarPestana(nuevaPestana) {
        setParametros({ pestana: nuevaPestana });
    }

    return (
        <section className="seccion">
            <div className="encabezado-seccion">
                <span className="etiqueta">GESTIÓN FINANCIERA</span>
                <h2>Panel de Finanzas</h2>
                <p>
                    Consulta los ingresos de ServiHome y las estadísticas generales
                    de la plataforma.
                </p>
            </div>

            <div className="pestanas" role="tablist" aria-label="Secciones financieras">
                <button
                    type="button"
                    role="tab"
                    aria-selected={pestana === 'finanzas'}
                    className={`pestana ${pestana === 'finanzas' ? 'pestana-activa' : ''}`}
                    onClick={() => cambiarPestana('finanzas')}
                >
                    Resumen financiero
                </button>

                <button
                    type="button"
                    role="tab"
                    aria-selected={pestana === 'estadisticas'}
                    className={`pestana ${pestana === 'estadisticas' ? 'pestana-activa' : ''}`}
                    onClick={() => cambiarPestana('estadisticas')}
                >
                    Estadísticas generales
                </button>
            </div>

            {pestana === 'finanzas' && <PanelFinanzas />}

            {pestana === 'estadisticas' && <PanelEstadisticas />}
        </section>
    );
}

export default Finanzas;
