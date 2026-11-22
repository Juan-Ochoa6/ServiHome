
import { Link } from 'react-router-dom';

function PoliticaCookies() {
  return (
    <section className="pagina-legal">
      <div className="legal-contenido">
        <span className="legal-etiqueta">SERVIHOME</span>

        <h1>Política de cookies</h1>

        <p className="legal-actualizacion">
          Última actualización: noviembre de 2026
        </p>

        <p>
          En ServiHome nos importa la privacidad de nuestros usuarios.
          Por eso, queremos explicarte qué tecnologías utilizamos,
          para qué sirven y cómo puedes administrar tus preferencias.
        </p>

        <h2>1. ¿Qué son las cookies?</h2>
        <p>
          Las cookies son pequeños archivos de información que los
          sitios web pueden almacenar en el navegador de un usuario.
          Permiten recordar información y facilitar el funcionamiento
          de una página web.
        </p>

        <h2>2. ¿Qué tecnologías utiliza ServiHome?</h2>
        <p>
          Actualmente, ServiHome utiliza el almacenamiento local del
          navegador (localStorage) para recordar la elección del
          usuario sobre el aviso de consentimiento.
        </p>
        <p>
          Esta información permite que el aviso no vuelva a aparecer
          cada vez que se visita la plataforma, siempre que el usuario
          no elimine los datos almacenados en su navegador.
        </p>

        <h2>3. Tipos de tecnologías y preferencias</h2>

        <h3>Necesarias</h3>
        <p>
          Son necesarias para recordar las preferencias de
          consentimiento y permitir el funcionamiento de las
          funcionalidades relacionadas con ellas.
        </p>

        <h3>Analíticas</h3>
        <p>
          Se contempla una categoría de tecnologías analíticas que
          podría utilizarse para comprender cómo interactúan los
          usuarios con la plataforma y mejorar sus funcionalidades.
          Actualmente, no se encuentra conectada una herramienta
          de analítica en el aviso de consentimiento.
        </p>

        <h2>4. ¿Cómo puedes administrar tus preferencias?</h2>
        <p>
          Al ingresar a ServiHome puedes aceptar todas las opciones,
          rechazar las opcionales o configurar tus preferencias.
          Las tecnologías opcionales no deben activarse sin la
          autorización correspondiente.
        </p>

        <p>
          También puedes eliminar los datos almacenados desde la
          configuración de tu navegador. Si lo haces, el aviso de
          consentimiento podrá aparecer nuevamente.
        </p>

        <h2>5. Cambios en esta política</h2>
        <p>
          ServiHome podrá actualizar esta política cuando cambien
          las funcionalidades de la plataforma o las tecnologías
          utilizadas. Publicaremos aquí la versión actualizada.
        </p>

        <h2>6. Contacto</h2>
        <p>
          Si tienes preguntas sobre esta política o sobre el uso
          de tecnologías de almacenamiento en ServiHome, puedes
          comunicarte con el equipo responsable del proyecto
          mediante los canales oficiales de contacto de la plataforma.
        </p>

        <div className="legal-volver">
          <Link to="/">Volver al inicio</Link>
        </div>
      </div>
    </section>
  );
}

export default PoliticaCookies;
