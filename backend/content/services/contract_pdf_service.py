"""
Generate a legally complete software development contract PDF (Colombia).

The contract is rendered in Spanish on portrait-A4 pages using the Project App
brand palette and Ubuntu typography.  All 19 clauses are included verbatim
from the standard *Contrato de Prestacion de Servicios* template.

Placeholders in the contract text are substituted with values from
``proposal.contract_params`` at generation time.
"""

import io
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content.services.pdf_utils import (
    ESMERALD,
    ESMERALD_80,
    GRAY_500,
    GRAY_300,
    LEMON,
    GREEN_LIGHT,
    MARGIN_L,
    MARGIN_R,
    MARGIN_T,
    MARGIN_B,
    PAGE_H,
    PAGE_W,
    CONTENT_W,
    _check_y,
    _draw_footer,
    _draw_header_bar,
    _draw_paragraphs,
    _font,
    _register_fonts,
    _strip_emoji,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contract text — full 19 clauses in Spanish
# ---------------------------------------------------------------------------
# Each entry is a dict with:
#   type        – 'intro' | 'clause'
#   heading     – (optional) clause title drawn in bold
#   paragraphs  – list of paragraph strings (may contain {placeholders})
#   subsections – (optional) list of sub-section dicts with:
#       heading    – sub-heading text
#       paragraphs – list of paragraph strings
#       items      – (optional) list of item strings (numbered / lettered)

CONTRACT_SECTIONS = [
    # ── Introductory paragraph ────────────────────────────────────
    {
        'type': 'intro',
        'paragraphs': [
            (
                'Entre las partes, por un lado {client_full_name} identificado con '
                'numero de cedula {client_cedula}, quien en adelante y para los '
                'efectos del presente contrato se denomina como EL CONTRATANTE, y '
                'por el otro, {contractor_full_name} identificado con numero de '
                'cedula {contractor_cedula}, quien en adelante y para los efectos '
                'del presente contrato se denomina como EL CONTRATISTA, ambos '
                'mayores de edad, identificados como aparece al pie de las firmas, '
                'hemos acordado suscribir este contrato de prestacion de servicios, '
                'el cual se regira por las siguientes clausulas:'
            ),
        ],
    },

    # ── Clausula 1 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA PRIMERA -- OBJETO DEL CONTRATO',
        'paragraphs': [
            (
                'EL CONTRATISTA se obliga a prestar sus servicios profesionales '
                'de desarrollo de software para EL CONTRATANTE, conforme a los '
                'terminos y condiciones establecidos en la propuesta comercial '
                'aprobada por las partes, la cual hace parte integral del '
                'presente contrato. El alcance especifico del proyecto, '
                'incluyendo funcionalidades, entregables y cronograma, sera el '
                'definido en dicha propuesta.'
            ),
        ],
    },

    # ── Clausula 2 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA SEGUNDA -- EJECUCION DEL CONTRATO',
        'paragraphs': [
            (
                'Para la adecuada ejecucion del objeto contractual, las partes '
                'acuerdan las siguientes condiciones:'
            ),
            (
                'El presente contrato tiene por objeto exclusivo el desarrollo '
                'del software descrito en la propuesta comercial. Cualquier '
                'funcionalidad, modulo o servicio adicional no contemplado en '
                'dicha propuesta debera ser acordado por escrito entre las '
                'partes mediante un otrosi al presente contrato, el cual '
                'podra generar costos adicionales.'
            ),
        ],
        'subsections': [
            {
                'heading': 'Paragrafo Primero -- Actividades',
                'paragraphs': [
                    'EL CONTRATISTA ejecutara las siguientes actividades principales:',
                ],
                'items': [
                    '1. Diseno: Elaboracion de la arquitectura del sistema, diseno de interfaces de usuario (UI/UX) y definicion de la estructura de datos conforme a los requerimientos aprobados.',
                    '2. Desarrollo: Programacion, codificacion e implementacion de las funcionalidades y modulos definidos en la propuesta comercial, utilizando las tecnologias acordadas.',
                    '3. Pruebas: Realizacion de pruebas funcionales, de integracion y de rendimiento para asegurar la calidad y el correcto funcionamiento del software.',
                    '4. Despliegue: Instalacion, configuracion y puesta en marcha del software en el ambiente de produccion del CONTRATANTE o en la infraestructura acordada.',
                    '5. Capacitacion: Entrega de documentacion tecnica y funcional, asi como sesiones de capacitacion al equipo del CONTRATANTE para el uso y administracion basica del software.',
                ],
            },
            {
                'heading': 'Paragrafo Segundo -- Plazo',
                'paragraphs': [
                    (
                        'El plazo de ejecucion del contrato sera el establecido en la '
                        'propuesta comercial aprobada por las partes. Dicho plazo comenzara '
                        'a contarse a partir de la fecha de firma del presente contrato y '
                        'del pago del anticipo pactado. Cualquier modificacion al '
                        'cronograma debera ser acordada por escrito entre las partes.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Tercero -- Entregables',
                'paragraphs': [
                    (
                        'Los entregables del proyecto seran los definidos en la propuesta '
                        'comercial. EL CONTRATISTA entregara cada componente conforme al '
                        'cronograma acordado. EL CONTRATANTE dispondra de un plazo de '
                        'cinco (5) dias habiles a partir de cada entrega para revisar y '
                        'aprobar o formular observaciones. Transcurrido dicho plazo sin '
                        'pronunciamiento, el entregable se considerara aprobado.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Cuarto -- Metodologia',
                'paragraphs': [
                    (
                        'El desarrollo se realizara bajo una metodologia agil que permita '
                        'entregas incrementales y retroalimentacion continua del '
                        'CONTRATANTE. Las reuniones de seguimiento, sprints y demos seran '
                        'programadas de comun acuerdo entre las partes.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Quinto -- Ambiente de trabajo',
                'paragraphs': [
                    (
                        'EL CONTRATISTA ejecutara sus actividades de manera remota, salvo '
                        'que las partes acuerden reuniones presenciales especificas. EL '
                        'CONTRATISTA utilizara sus propias herramientas, equipos y '
                        'licencias de software necesarios para la ejecucion del contrato.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Sexto -- Comunicacion',
                'paragraphs': [
                    (
                        'Las partes mantendran comunicacion fluida a traves de los canales '
                        'acordados (correo electronico, plataforma de gestion de proyectos, '
                        'videollamadas). EL CONTRATISTA informara oportunamente sobre el '
                        'avance del proyecto, riesgos identificados y cualquier situacion '
                        'que pueda afectar el cumplimiento del cronograma.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Septimo -- Control de cambios',
                'paragraphs': [
                    (
                        'Toda solicitud de cambio que modifique el alcance, cronograma o '
                        'presupuesto del proyecto debera ser documentada y aprobada por '
                        'escrito por ambas partes antes de su implementacion. EL '
                        'CONTRATISTA evaluara el impacto del cambio y presentara una '
                        'propuesta de ajuste que incluya tiempo y costo adicional, si '
                        'aplica.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Octavo -- Garantia tecnica',
                'paragraphs': [
                    (
                        'EL CONTRATISTA garantiza que el software entregado funcionara '
                        'conforme a las especificaciones aprobadas durante un periodo de '
                        'treinta (30) dias calendario posteriores a la entrega final y '
                        'aprobacion del proyecto. Durante este periodo, EL CONTRATISTA '
                        'corregira sin costo adicional cualquier defecto o error '
                        'atribuible a su desarrollo. Esta garantia no cubre errores '
                        'derivados de modificaciones realizadas por terceros, uso '
                        'inadecuado del software o cambios en la infraestructura del '
                        'CONTRATANTE.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Noveno -- Soporte post-entrega',
                'paragraphs': [
                    (
                        'Una vez finalizado el periodo de garantia, EL CONTRATANTE podra '
                        'contratar servicios adicionales de soporte, mantenimiento o '
                        'evolucion del software mediante acuerdos separados. EL '
                        'CONTRATISTA presentara una propuesta de costos para dichos '
                        'servicios adicionales.'
                    ),
                ],
            },
        ],
    },

    # ── Clausula 3 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA TERCERA -- PRECIO Y FORMA DE PAGO',
        'paragraphs': [
            (
                'El valor total del contrato sera el establecido en la propuesta '
                'comercial aprobada por las partes. Los pagos se realizaran '
                'conforme al esquema de hitos o cuotas definido en dicha propuesta.'
            ),
        ],
        'subsections': [
            {
                'heading': 'Paragrafo Primero -- Forma de pago',
                'paragraphs': [
                    (
                        'Los pagos se realizaran mediante transferencia bancaria a la '
                        'cuenta de {bank_name} {bank_account_type} No. '
                        '{bank_account_number} a nombre de EL CONTRATISTA identificado '
                        'con cedula {contractor_cedula}. El pago se considerara '
                        'efectuado en la fecha en que los fondos sean acreditados en '
                        'dicha cuenta.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Segundo -- Mora en el pago',
                'paragraphs': [
                    (
                        'En caso de mora en cualquiera de los pagos pactados superior a '
                        'diez (10) dias calendario, EL CONTRATISTA podra suspender la '
                        'ejecucion del proyecto hasta tanto se regularice el pago, sin '
                        'que ello constituya incumplimiento de su parte. El cronograma '
                        'se ajustara en proporcion al tiempo de suspension.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Tercero -- Impuestos',
                'paragraphs': [
                    (
                        'Cada parte sera responsable de sus propias obligaciones '
                        'tributarias derivadas del presente contrato. EL CONTRATISTA '
                        'emitira la facturacion o cuenta de cobro correspondiente a '
                        'cada pago, conforme a la normatividad vigente.'
                    ),
                ],
            },
        ],
    },

    # ── Clausula 4 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA CUARTA -- SUBCONTRATACION',
        'paragraphs': [
            (
                'EL CONTRATISTA podra subcontratar parcialmente la ejecucion de '
                'actividades especificas del proyecto, siempre que mantenga la '
                'responsabilidad total sobre la calidad y el cumplimiento de los '
                'entregables frente a EL CONTRATANTE. La subcontratacion no '
                'requerira autorizacion previa del CONTRATANTE, salvo que se '
                'trate de la totalidad del objeto contractual.'
            ),
        ],
    },

    # ── Clausula 5 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA QUINTA -- SUPERVISION',
        'paragraphs': [
            (
                'EL CONTRATANTE podra designar un representante o supervisor para '
                'el seguimiento del proyecto, quien servira como punto de contacto '
                'principal para la comunicacion con EL CONTRATISTA. Dicho '
                'supervisor tendra la facultad de aprobar entregables, solicitar '
                'ajustes dentro del alcance contratado y participar en las '
                'reuniones de seguimiento. La supervision no implica subordinacion '
                'laboral ni direccion tecnica sobre la forma en que EL CONTRATISTA '
                'ejecuta sus actividades.'
            ),
        ],
    },

    # ── Clausula 6 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA SEXTA -- EXCLUSION DE LA RELACION LABORAL',
        'paragraphs': [
            (
                'El presente contrato es de naturaleza civil y de prestacion de '
                'servicios. No genera relacion laboral alguna entre las partes, '
                'ni vinculo de subordinacion o dependencia. EL CONTRATISTA actua '
                'como profesional independiente, asume sus propios riesgos y es '
                'responsable de sus obligaciones en materia de seguridad social, '
                'salud y pensiones conforme a la legislacion colombiana vigente.'
            ),
        ],
    },

    # ── Clausula 7 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA SEPTIMA -- OBLIGACIONES DEL CONTRATISTA',
        'paragraphs': [
            'Son obligaciones de EL CONTRATISTA:',
        ],
        'subsections': [
            {
                'heading': None,
                'paragraphs': [],
                'items': [
                    'a) Ejecutar el objeto del contrato con diligencia, calidad profesional y dentro de los plazos acordados.',
                    'b) Entregar el software funcional conforme a las especificaciones aprobadas en la propuesta comercial.',
                    'c) Informar oportunamente sobre cualquier riesgo, impedimento o situacion que pueda afectar la ejecucion del proyecto.',
                    'd) Mantener la confidencialidad de toda la informacion del CONTRATANTE a la que tenga acceso en desarrollo del contrato.',
                    'e) Proveer la documentacion tecnica y funcional del software desarrollado.',
                    'f) Cumplir con las normas de proteccion de datos personales aplicables.',
                    'g) Emitir la facturacion o cuenta de cobro correspondiente a cada pago.',
                ],
            },
        ],
    },

    # ── Clausula 8 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA OCTAVA -- OBLIGACIONES DEL CONTRATANTE',
        'paragraphs': [
            'Son obligaciones de EL CONTRATANTE:',
        ],
        'subsections': [
            {
                'heading': None,
                'paragraphs': [],
                'items': [
                    'a) Suministrar oportunamente la informacion, accesos y recursos necesarios para la ejecucion del proyecto.',
                    'b) Realizar los pagos en los plazos y condiciones pactados en la propuesta comercial.',
                    'c) Designar un representante o punto de contacto para la comunicacion con EL CONTRATISTA.',
                    'd) Revisar y aprobar los entregables dentro de los plazos establecidos, o formular observaciones oportunas y precisas.',
                    'e) No utilizar el software desarrollado para fines distintos a los acordados, ni permitir su uso por terceros no autorizados durante la vigencia del contrato.',
                ],
            },
        ],
    },

    # ── Clausula 9 ────────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA NOVENA -- DERECHOS PATRIMONIALES',
        'paragraphs': [
            (
                'Una vez recibido el pago total del valor del contrato, EL '
                'CONTRATISTA cedera a EL CONTRATANTE los derechos patrimoniales '
                'de autor sobre el software desarrollado especificamente para '
                'el proyecto, incluyendo el codigo fuente, la documentacion '
                'tecnica y los disenos creados en ejecucion del presente '
                'contrato.'
            ),
        ],
        'subsections': [
            {
                'heading': 'Paragrafo Primero',
                'paragraphs': [
                    (
                        'Se exceptuan de esta cesion las librerias, frameworks, '
                        'herramientas, componentes reutilizables y metodologias '
                        'preexistentes de EL CONTRATISTA que hayan sido '
                        'utilizadas en el desarrollo del proyecto. Sobre estos '
                        'elementos, EL CONTRATANTE recibira una licencia de uso '
                        'perpetua, no exclusiva e intransferible, limitada al '
                        'funcionamiento del software contratado.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Segundo',
                'paragraphs': [
                    (
                        'Los derechos morales de autor corresponden de manera '
                        'irrenunciable e inalienable a EL CONTRATISTA como '
                        'creador del software, conforme a la legislacion '
                        'colombiana de derechos de autor.'
                    ),
                ],
            },
        ],
    },

    # ── Clausula 10 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA -- CONFIDENCIALIDAD',
        'paragraphs': [
            (
                'Las partes se comprometen a mantener estricta confidencialidad '
                'sobre toda la informacion tecnica, comercial, financiera y '
                'estrategica a la que tengan acceso con ocasion del presente '
                'contrato. Esta obligacion se extiende a los empleados, '
                'subcontratistas y asesores de cada parte.'
            ),
            (
                'La obligacion de confidencialidad permanecera vigente durante '
                'la ejecucion del contrato y por un periodo de dos (2) anos '
                'posteriores a su terminacion.'
            ),
            'No se considerara informacion confidencial aquella que:',
        ],
        'subsections': [
            {
                'heading': None,
                'paragraphs': [],
                'items': [
                    'a) Sea o se convierta en informacion de dominio publico sin culpa de la parte receptora.',
                    'b) Haya sido conocida por la parte receptora con anterioridad a su divulgacion, sin obligacion de confidencialidad.',
                    'c) Sea recibida legitimamente de un tercero sin restriccion de divulgacion.',
                    'd) Deba ser divulgada por orden judicial o requerimiento de autoridad competente.',
                ],
            },
        ],
    },

    # ── Clausula 11 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA PRIMERA -- PROTECCION DE DATOS',
        'paragraphs': [
            (
                'Las partes se comprometen a cumplir con la Ley 1581 de 2012 '
                'y sus decretos reglamentarios en materia de proteccion de '
                'datos personales. En particular:'
            ),
        ],
        'subsections': [
            {
                'heading': None,
                'paragraphs': [],
                'items': [
                    'a) EL CONTRATISTA tratara los datos personales del CONTRATANTE y sus usuarios unicamente para los fines del presente contrato.',
                    'b) EL CONTRATISTA implementara las medidas tecnicas y organizativas adecuadas para proteger los datos personales contra acceso no autorizado, perdida o destruccion.',
                    'c) Al terminar el contrato, EL CONTRATISTA devolvera o eliminara los datos personales del CONTRATANTE que obren en su poder, salvo obligacion legal de conservacion.',
                    'd) En caso de incidente de seguridad que afecte datos personales, la parte que lo detecte informara a la otra en un plazo maximo de cuarenta y ocho (48) horas.',
                    'e) Cada parte sera responsable del tratamiento de datos personales que realice en calidad de responsable o encargado, conforme a la normatividad vigente.',
                ],
            },
        ],
    },

    # ── Clausula 12 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA SEGUNDA -- MODIFICACIONES',
        'paragraphs': [
            (
                'Toda modificacion al presente contrato debera constar por '
                'escrito y ser firmada por ambas partes mediante un otrosi. '
                'Ningun acuerdo verbal o comunicacion informal tendra la '
                'capacidad de modificar los terminos y condiciones aqui '
                'pactados.'
            ),
        ],
    },

    # ── Clausula 13 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA TERCERA -- ACUERDO',
        'paragraphs': [
            (
                'El presente contrato, junto con la propuesta comercial '
                'aprobada y sus anexos, constituye el acuerdo completo entre '
                'las partes respecto al objeto contractual y reemplaza '
                'cualquier negociacion, acuerdo o comunicacion previa, ya sea '
                'oral o escrita, relacionada con el mismo.'
            ),
        ],
    },

    # ── Clausula 14 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA CUARTA -- NOTIFICACION',
        'paragraphs': [
            (
                'Toda notificacion o comunicacion formal relacionada con el '
                'presente contrato debera realizarse por escrito a las '
                'siguientes direcciones de correo electronico:'
            ),
            'EL CONTRATANTE: {client_email}',
            'EL CONTRATISTA: {contractor_email}',
            (
                'Las notificaciones se consideraran realizadas en la fecha '
                'de envio del correo electronico, siempre que se pueda '
                'acreditar su recepcion. Cualquier cambio en los datos de '
                'contacto debera ser comunicado a la otra parte con al menos '
                'cinco (5) dias habiles de anticipacion.'
            ),
        ],
    },

    # ── Clausula 15 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA QUINTA -- TERMINACION ANTICIPADA',
        'paragraphs': [],
        'subsections': [
            {
                'heading': 'Paragrafo Primero',
                'paragraphs': [
                    (
                        'Cualquiera de las partes podra dar por terminado el '
                        'presente contrato de manera anticipada, mediante '
                        'comunicacion escrita dirigida a la otra parte con al '
                        'menos treinta (30) dias calendario de anticipacion.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Segundo',
                'paragraphs': [
                    (
                        'En caso de terminacion anticipada por parte del '
                        'CONTRATANTE, este debera pagar a EL CONTRATISTA el '
                        'valor proporcional de los servicios efectivamente '
                        'prestados hasta la fecha de terminacion, incluyendo '
                        'los entregables parciales completados.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Tercero',
                'paragraphs': [
                    (
                        'En caso de terminacion anticipada por parte del '
                        'CONTRATISTA, este debera entregar al CONTRATANTE '
                        'todos los avances, codigo fuente y documentacion '
                        'generados hasta la fecha de terminacion, y reembolsar '
                        'la parte proporcional de los pagos recibidos que no '
                        'correspondan a servicios efectivamente prestados.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Cuarto',
                'paragraphs': [
                    (
                        'Las obligaciones de confidencialidad, proteccion de '
                        'datos y derechos de propiedad intelectual subsistiran '
                        'a la terminacion del contrato en los terminos '
                        'establecidos en las clausulas correspondientes.'
                    ),
                ],
            },
        ],
    },

    # ── Clausula 16 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA SEXTA -- INCUMPLIMIENTO',
        'paragraphs': [],
        'subsections': [
            {
                'heading': 'Paragrafo Primero',
                'paragraphs': [
                    (
                        'En caso de incumplimiento de cualquiera de las '
                        'obligaciones del presente contrato, la parte '
                        'cumplida debera requerir por escrito a la parte '
                        'incumplida, otorgandole un plazo razonable no '
                        'inferior a quince (15) dias habiles para subsanar '
                        'el incumplimiento.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Segundo',
                'paragraphs': [
                    (
                        'Si transcurrido el plazo otorgado el incumplimiento '
                        'persiste, la parte cumplida podra dar por terminado '
                        'el contrato y exigir la indemnizacion de los '
                        'perjuicios causados, conforme a las reglas generales '
                        'del derecho civil colombiano.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Tercero',
                'paragraphs': [
                    (
                        'No se considerara incumplimiento el retraso o la '
                        'imposibilidad de ejecucion derivada de eventos de '
                        'fuerza mayor o caso fortuito debidamente acreditados, '
                        'tales como desastres naturales, conflictos armados, '
                        'pandemias, fallos masivos de infraestructura '
                        'tecnologica o actos de autoridad que impidan la '
                        'ejecucion. En tales casos, los plazos se suspenderan '
                        'por el tiempo que dure el evento.'
                    ),
                ],
            },
        ],
    },

    # ── Clausula 17 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA SEPTIMA -- RESOLUCION DE CONFLICTOS',
        'paragraphs': [
            (
                'Las partes acuerdan resolver cualquier controversia derivada '
                'del presente contrato de la siguiente manera:'
            ),
        ],
        'subsections': [
            {
                'heading': None,
                'paragraphs': [],
                'items': [
                    '1. Negociacion directa: Las partes intentaran resolver la controversia de buena fe mediante negociacion directa durante un plazo de treinta (30) dias calendario.',
                    '2. Mediacion: Si la negociacion directa no prospera, las partes podran acudir a un mediador neutral de comun acuerdo.',
                    '3. Arbitraje o jurisdiccion ordinaria: En caso de no lograr acuerdo mediante los mecanismos anteriores, las partes podran someter la controversia a la jurisdiccion ordinaria de la ciudad de {contract_city}, Colombia.',
                ],
            },
        ],
    },

    # ── Clausula 18 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA OCTAVA -- MERITO EJECUTIVO',
        'paragraphs': [
            (
                'El presente contrato presta merito ejecutivo para el '
                'cumplimiento de las obligaciones aqui contenidas, de '
                'conformidad con el articulo 422 del Codigo General del '
                'Proceso.'
            ),
        ],
    },

    # ── Clausula 19 ───────────────────────────────────────────────
    {
        'type': 'clause',
        'heading': 'CLAUSULA DECIMA NOVENA -- LIMITACION DE RESPONSABILIDAD',
        'paragraphs': [
            (
                'La responsabilidad total de EL CONTRATISTA frente a EL '
                'CONTRATANTE por cualquier concepto derivado del presente '
                'contrato no excedera el valor total efectivamente pagado '
                'por el CONTRATANTE al momento de la reclamacion.'
            ),
        ],
        'subsections': [
            {
                'heading': 'Paragrafo Primero',
                'paragraphs': [
                    (
                        'EL CONTRATISTA no sera responsable por danos '
                        'indirectos, consecuenciales, lucro cesante o perdida '
                        'de datos derivados del uso del software, salvo en '
                        'casos de dolo o culpa grave.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Segundo',
                'paragraphs': [
                    (
                        'EL CONTRATISTA no sera responsable por el '
                        'funcionamiento del software en ambientes tecnologicos '
                        'distintos a los especificados en la propuesta '
                        'comercial, ni por errores derivados de '
                        'modificaciones realizadas por terceros sin su '
                        'autorizacion.'
                    ),
                ],
            },
            {
                'heading': 'Paragrafo Tercero',
                'paragraphs': [
                    (
                        'EL CONTRATANTE reconoce que el software se entrega '
                        '"tal cual" una vez finalizada la garantia tecnica, y '
                        'que EL CONTRATISTA no garantiza que el software este '
                        'libre de todo error o que funcione de manera '
                        'ininterrumpida. El mantenimiento y soporte '
                        'posterior a la garantia seran objeto de acuerdos '
                        'separados.'
                    ),
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_contract_pdf(proposal) -> bytes | None:
    """Generate a contract PDF from *proposal.contract_params* and return raw bytes.

    Returns ``None`` if generation fails (logs the error).
    """
    try:
        raw_params = getattr(proposal, 'contract_params', None) or {}

        # Build params dict with sensible defaults
        params = {
            'contractor_full_name': raw_params.get('contractor_full_name', '_______________'),
            'contractor_cedula': raw_params.get('contractor_cedula', '_______________'),
            'contractor_email': raw_params.get('contractor_email', '_______________'),
            'bank_name': raw_params.get('bank_name', '_______________'),
            'bank_account_type': raw_params.get('bank_account_type', 'Ahorros'),
            'bank_account_number': raw_params.get('bank_account_number', '_______________'),
            'contract_city': raw_params.get('contract_city', 'Medellin'),
            'client_full_name': raw_params.get('client_full_name', '_______________'),
            'client_cedula': raw_params.get('client_cedula', '_______________'),
            'client_email': raw_params.get('client_email', '_______________'),
            'contract_date': raw_params.get('contract_date', ''),
        }

        client_name = params['client_full_name']

        _register_fonts()
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        # Page state dict (shared across helpers)
        ps = {'num': 1, 'client': client_name}

        # ── First page ────────────────────────────────────────────
        _draw_header_bar(c)
        y = PAGE_H - MARGIN_T

        # Title
        c.setFont(_font('light'), 22)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, 'CONTRATO DE PRESTACION')
        y -= 28
        c.drawString(MARGIN_L, y, 'DE SERVICIOS')
        y -= 36

        # Thin accent line
        c.setStrokeColor(LEMON)
        c.setLineWidth(2)
        c.line(MARGIN_L, y + 6, MARGIN_L + 80, y + 6)
        y -= 18

        # Party header
        c.setFont(_font('bold'), 10)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, f'ENTRE: {params["client_full_name"]} (EL CONTRATANTE)')
        y -= 16
        c.drawString(MARGIN_L, y, f'Y: {params["contractor_full_name"]} (EL CONTRATISTA)')
        y -= 24

        # Date (if provided)
        if params['contract_date']:
            c.setFont(_font('regular'), 9)
            c.setFillColor(GRAY_500)
            c.drawString(MARGIN_L, y, f'Fecha: {params["contract_date"]}')
            y -= 20

        # ── Render sections ───────────────────────────────────────
        for section in CONTRACT_SECTIONS:
            sec_type = section.get('type', 'clause')
            heading = section.get('heading')
            paragraphs = section.get('paragraphs', [])
            subsections = section.get('subsections', [])

            # Format placeholders in paragraphs
            fmt_paragraphs = []
            for p in paragraphs:
                try:
                    fmt_paragraphs.append(p.format(**params))
                except (KeyError, IndexError):
                    fmt_paragraphs.append(p)

            if sec_type == 'intro':
                # Intro paragraph — no heading
                y = _check_y(c, y, ps, need=60)
                y = _draw_paragraphs(
                    c, y, fmt_paragraphs, ps=ps,
                    color=ESMERALD_80, font_size=9, leading=13,
                )
                y -= 12
                continue

            # ── Clause heading ────────────────────────────────────
            y = _check_y(c, y, ps, need=60)
            c.setFont(_font('bold'), 12)
            c.setFillColor(ESMERALD)
            c.drawString(MARGIN_L, y, heading)
            y -= 20

            # Main paragraphs
            if fmt_paragraphs:
                y = _draw_paragraphs(
                    c, y, fmt_paragraphs, ps=ps,
                    color=ESMERALD_80, font_size=9, leading=13,
                )
                y -= 4

            # ── Subsections (paragrafos, lettered/numbered lists) ─
            for sub in subsections:
                sub_heading = sub.get('heading')
                sub_paragraphs = sub.get('paragraphs', [])
                sub_items = sub.get('items', [])

                # Format placeholders
                fmt_sub_paragraphs = []
                for p in sub_paragraphs:
                    try:
                        fmt_sub_paragraphs.append(p.format(**params))
                    except (KeyError, IndexError):
                        fmt_sub_paragraphs.append(p)

                fmt_sub_items = []
                for item in sub_items:
                    try:
                        fmt_sub_items.append(item.format(**params))
                    except (KeyError, IndexError):
                        fmt_sub_items.append(item)

                if sub_heading:
                    y = _check_y(c, y, ps, need=40)
                    c.setFont(_font('bold'), 10)
                    c.setFillColor(ESMERALD)
                    c.drawString(MARGIN_L + 12, y, sub_heading)
                    y -= 16

                if fmt_sub_paragraphs:
                    y = _draw_paragraphs(
                        c, y, fmt_sub_paragraphs, ps=ps,
                        color=ESMERALD_80, font_size=9, leading=13,
                    )
                    y -= 2

                if fmt_sub_items:
                    y = _draw_paragraphs(
                        c, y, fmt_sub_items, ps=ps,
                        color=ESMERALD_80, font_size=9, leading=13,
                        x=MARGIN_L + 16,
                        max_width=CONTENT_W - 16,
                    )
                    y -= 2

            y -= 12

        # ── Signature block ───────────────────────────────────────
        y = _check_y(c, y, ps, need=160)
        y -= 20

        c.setFont(_font('bold'), 11)
        c.setFillColor(ESMERALD)
        c.drawString(MARGIN_L, y, 'EN CONSTANCIA DE LO ANTERIOR,')
        y -= 14
        c.setFont(_font('regular'), 9)
        c.setFillColor(ESMERALD_80)
        c.drawString(
            MARGIN_L, y,
            'las partes firman el presente contrato en dos (2) ejemplares del mismo tenor.',
        )
        y -= 40

        # Two-column signature layout
        col1_x = MARGIN_L
        col2_x = MARGIN_L + CONTENT_W / 2 + 10
        sig_width = CONTENT_W / 2 - 20

        # Signature lines
        c.setStrokeColor(GRAY_300)
        c.setLineWidth(0.6)
        c.line(col1_x, y, col1_x + sig_width, y)
        c.line(col2_x, y, col2_x + sig_width, y)
        y -= 14

        c.setFont(_font('bold'), 9)
        c.setFillColor(ESMERALD)
        c.drawString(col1_x, y, 'EL CONTRATANTE')
        c.drawString(col2_x, y, 'EL CONTRATISTA')
        y -= 14

        c.setFont(_font('regular'), 8)
        c.setFillColor(ESMERALD_80)
        c.drawString(col1_x, y, params['client_full_name'])
        c.drawString(col2_x, y, params['contractor_full_name'])
        y -= 12
        c.drawString(col1_x, y, f'C.C. {params["client_cedula"]}')
        c.drawString(col2_x, y, f'C.C. {params["contractor_cedula"]}')

        # ── Finalize ──────────────────────────────────────────────
        _draw_footer(c, ps['num'], client_name=ps['client'])
        c.save()
        return buf.getvalue()

    except Exception:
        logger.exception('Failed to generate contract PDF for proposal %s', getattr(proposal, 'pk', '?'))
        return None
