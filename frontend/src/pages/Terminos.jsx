
import { Link } from 'react-router-dom';

function Terminos() {
  return (
    <section className="pagina-legal">
      <div className="legal-contenido">
        <span className="legal-etiqueta">SERVIHOME</span>

        <h1>Términos y condiciones</h1>

        <p className="legal-actualizacion">
          Última actualización: noviembre de 2026
        </p>

        <p>
          Bienvenido a ServiHome. Estos términos y condiciones
          establecen las reglas para acceder y utilizar nuestra
          plataforma. Al registrarte o utilizar nuestros servicios,
          manifiestas que has leído y aceptado estas condiciones.
        </p>

        <h2>1. ¿Qué es ServiHome?</h2>
        <p>
          ServiHome es una plataforma digital cuyo propósito es
          facilitar el contacto entre personas que necesitan
          servicios para el hogar y profesionales independientes
          que ofrecen dichos servicios.
        </p>
        <p>
          La plataforma permite consultar servicios, conocer
          profesionales, enviar solicitudes, coordinar trabajos
          y compartir evaluaciones sobre las experiencias.
        </p>

        <h2>2. Registro y cuentas de usuario</h2>
        <p>
          Para utilizar determinadas funcionalidades es necesario
          crear una cuenta y proporcionar información veraz,
          actualizada y completa.
        </p>
        <p>
          Cada usuario es responsable de mantener la
          confidencialidad de sus credenciales y de las
          actividades realizadas desde su cuenta.
        </p>
        <p>
          Si detectas un uso no autorizado de tu cuenta,
          debes comunicarlo al equipo responsable de ServiHome.
        </p>

        <h2>3. Tipos de usuarios</h2>

        <h3>Clientes</h3>
        <p>
          Los clientes pueden consultar los servicios disponibles,
          revisar perfiles profesionales y enviar solicitudes
          describiendo sus necesidades.
        </p>

        <h3>Profesionales</h3>
        <p>
          Los profesionales pueden publicar información sobre
          sus servicios, experiencia y disponibilidad. Se
          comprometen a proporcionar información veraz y a
          actuar de manera responsable frente a las solicitudes
          recibidas.
        </p>

        <h2>4. Uso adecuado de la plataforma</h2>
        <p>
          Los usuarios se comprometen a utilizar ServiHome de
          manera legal, respetuosa y responsable.
        </p>
        <p>No está permitido:</p>
        <ul>
          <li>Publicar información falsa, engañosa o fraudulenta.</li>
          <li>Suplantar la identidad de otras personas.</li>
          <li>Utilizar la plataforma para actividades ilegales.</li>
          <li>Acosar, amenazar o perjudicar a otros usuarios.</li>
          <li>Intentar acceder sin autorización a cuentas o sistemas.</li>
          <li>Compartir contenido que vulnere derechos de terceros.</li>
        </ul>

        <h2>5. Solicitudes y prestación de servicios</h2>
        <p>
          El envío de una solicitud a través de ServiHome no
          garantiza que un profesional la acepte ni que el
          servicio llegue a realizarse.
        </p>
        <p>
          Los usuarios deben coordinar y confirmar directamente
          las condiciones del trabajo, incluyendo su alcance,
          fecha, horario, precio y demás aspectos necesarios.
        </p>
        <p>
          Cada profesional es responsable de la calidad,
          seguridad y cumplimiento de los servicios que ofrece,
          dentro del marco de sus obligaciones legales.
        </p>

        <h2>6. Responsabilidades de los usuarios</h2>
        <p>
          Los clientes y profesionales deben comunicarse con
          respeto, proporcionar información correcta y cumplir
          los acuerdos que establezcan entre ellos.
        </p>
        <p>
          Los usuarios deben verificar que las condiciones
          acordadas sean claras antes de iniciar cualquier
          trabajo.
        </p>

        <h2>7. Evaluaciones y opiniones</h2>
        <p>
          Las evaluaciones deben corresponder a experiencias
          reales y expresarse de manera respetuosa.
          No se permite publicar opiniones falsas, ofensivas
          o utilizadas para perjudicar a otros usuarios.
        </p>

        <h2>8. Disponibilidad de la plataforma</h2>
        <p>
          ServiHome trabaja para mantener la plataforma
          disponible y funcionando correctamente. Sin embargo,
          pueden presentarse interrupciones por mantenimiento,
          actualizaciones, fallos técnicos o circunstancias
          ajenas al equipo responsable.
        </p>

        <h2>9. Propiedad intelectual</h2>
        <p>
          Los elementos propios de ServiHome, incluyendo su
          identidad visual, diseño, textos y componentes de
          software, están protegidos por las normas aplicables
          de propiedad intelectual.
        </p>
        <p>
          Los usuarios conservan los derechos que les
          correspondan sobre el contenido que publican,
          y autorizan su utilización dentro de la plataforma
          en la medida necesaria para prestar sus funcionalidades.
        </p>

        <h2>10. Privacidad y tratamiento de datos</h2>
        <p>
          El tratamiento de los datos personales de los usuarios
          se realizará conforme a la política de privacidad
          de ServiHome y a la normativa colombiana aplicable.
        </p>

        <h2>11. Suspensión de cuentas</h2>
        <p>
          ServiHome podrá restringir o suspender el acceso a
          una cuenta cuando existan indicios de incumplimiento
          de estos términos, uso indebido de la plataforma
          o riesgos para otros usuarios, respetando las
          disposiciones legales aplicables.
        </p>

        <h2>12. Modificaciones</h2>
        <p>
          Estos términos podrán actualizarse cuando cambien
          las funcionalidades de ServiHome o las condiciones
          de uso. La versión vigente estará disponible en
          esta página.
        </p>

        <h2>13. Legislación aplicable</h2>
        <p>
          Estos términos se interpretarán de acuerdo con
          la legislación vigente de la República de Colombia,
          sin perjuicio de los derechos irrenunciables
          que correspondan a los usuarios.
        </p>

        <h2>14. Contacto</h2>
        <p>
          Si tienes preguntas sobre estos términos y condiciones,
          puedes comunicarte con el equipo responsable de
          ServiHome mediante los canales oficiales de contacto
          de la plataforma.
        </p>

        <div className="legal-volver">
          <Link to="/">Volver al inicio</Link>
        </div>
      </div>
    </section>
  );
}

export default Terminos;
