# Fake Data Coverage — ProjectApp

> Contrato de cobertura de fake data por feature y por modelo. Sirve como checklist
> de regresión: cada vez que se añade un modelo/feature, agregar su fila y asegurar
> que un comando lo puebla con sentido de negocio.
>
> **Generación:** `python manage.py create_fake_data --count 50` (orquestador único).
> **Limpieza:** `python manage.py delete_fake_data --confirm`.
> **Skill:** `fake-data-refresh` (bloquea producción).

## Criterios auditados

1. **Existe** — hay un comando que crea datos para la feature.
2. **Suficiente** — volumen alto (40–60) para paginación, filtros y "jugar".
3. **Al día** — cubre los modelos/relaciones actuales (no quedó atrás vs. migraciones).
4. **Sentido de negocio** — datos y relaciones coherentes (estados, fechas, totales que suman).

## Matriz por feature (estado objetivo tras nivelación)

| # | Feature | Existe | Suficiente | Al día | Negocio | Comando responsable |
|---|---------|:--:|:--:|:--:|:--:|---------|
| 1 | Proposals & Negotiation | ✅ | ✅ | ✅ | ✅ | `create_fake_proposals` |
| 2 | Blog & Marketing | ✅ | ✅ | ✅ | ✅ | `create_fake_blog_posts` |
| 3 | Portfolio | ✅ | ✅ | ✅ | ✅ | `create_fake_portfolio` *(nuevo)* |
| 4 | Diagnostics | ✅ | ✅ | ✅ | ✅ | `create_fake_diagnostics` *(ahora cableado)* |
| 5 | Documents & Billing | ✅ | ✅ | ✅ | ✅ | `create_fake_documents` *(nuevo)* |
| 6 | Projects & Delivery | ✅ | ✅ | ✅ | ✅ | `seed_platform_data` + `enrich_platform_data` |
| 7 | Change Management | ✅ | ✅ | ✅ | ✅ | `seed_platform_data` |
| 8 | Quality Assurance (Bugs) | ✅ | ✅ | ✅ | ✅ | `seed_platform_data` |
| 9 | Notifications | ✅ | ✅ | ✅ | ✅ | `enrich_platform_data` |
| 10 | Hosting & Billing | ✅ | ✅ | ✅ | ✅ | `seed_platform_data` + `enrich_platform_data` (PaymentHistory) |
| 11 | Team Management (Tasks) | ✅ | ✅ | ✅ | ✅ | `create_fake_tasks` *(+ alerts/comments)* |
| 12 | User & Auth | ✅ | ✅ | ✅ | ✅ | `seed_platform_data` + `seed_demo_clients` |
| 13 | Admin Settings | ✅ | ✅ | ✅ | ✅ | `enrich_platform_data` + migraciones de datos |

## Cobertura por modelo

Comando: `P`=create_fake_proposals · `B`=blog · `PF`=portfolio · `D`=documents ·
`DG`=diagnostics · `T`=tasks · `SP`=seed_platform_data · `EP`=enrich_platform_data ·
`DC`=seed_demo_clients · `M`=migración de datos.

| Feature | Modelo | Cmd | Count objetivo | Relaciones pobladas |
|---------|--------|:--:|:--:|---------|
| Proposals | BusinessProposal | P | ~count | secciones, view events, change logs, share links, docs |
| Proposals | ProposalSection | P | 15×prop | FK proposal |
| Proposals | ProposalRequirementGroup/Item | P | varias | FK proposal/group |
| Proposals | ProposalViewEvent/SectionView | P | 1–6×prop | FK proposal/event |
| Proposals | ProposalChangeLog | P | 1–8×prop | FK proposal |
| Proposals | ProposalShareLink | P | 0–1×prop | FK proposal |
| Proposals | ProposalDocument | P | negociando | FK proposal |
| Proposals | ProposalProjectStage | P | aceptadas | FK proposal |
| Blog | BlogPost | B | ~count | bilingüe, SEO, JSON |
| Portfolio | PortfolioWork | PF | ~count | bilingüe, content_json problem/solution/results |
| Diagnostics | WebAppDiagnostic | DG | ~count | client, secciones, views, estados |
| Diagnostics | DiagnosticSection/ViewEvent/SectionView/ChangeLog | DG | derivadas | FK diagnostic |
| Documents | IssuerProfile | D | 1 | emisor legal |
| Documents | DocumentFolder | D | árbol (8) | self-FK parent jerárquico |
| Documents | DocumentTag | D | 6 | M2M con documents |
| Documents | Document | D | ~count | folder, tags, project/client, items |
| Documents | DocumentItem | D | 1–3×doc | FK document; totales suman |
| Documents | DocumentCollectionAccount | D | por cuenta | OneToOne; snapshots payer/customer |
| Documents | DocumentPaymentMethod | D | 1×cuenta | FK document; is_primary |
| Documents | DocumentNumberSequence | D | por issuer/año | consecutivo public_number |
| Documents | DocumentType | M | 2 (markdown, collection_account) | catálogo (preservado) |
| Projects | Project / ProjectPhase | SP | varios | client, proposal |
| Projects | Requirement (+Comment/History) | SP | 40–55×proj | epics, estados kanban |
| Projects | Deliverable (+Version) | SP | 2–8×proj | FK project |
| Projects | DeliverableFile | EP | ~½ deliverables | FK deliverable |
| Projects | DeliverableClientFolder/Upload | EP | ~40% deliverables | FK deliverable/folder |
| Projects | DataModelEntity | SP | ~10 | sincronizado de propuesta |
| Projects | ProjectDataModelEntity | EP | 5×proj | estado real del proyecto |
| Change Mgmt | ChangeRequest (+Comment) | SP | 5–6×proj | estados, respuestas |
| QA | BugReport (+Comment) | SP | 5–9×proj | severidad, entorno |
| Notifications | Notification | EP | ≥40 | tipos variados, read/unread |
| Hosting | HostingSubscription | SP | 1×proj | OneToOne project |
| Hosting | Payment | SP | 2–3×sub | estados |
| Hosting | PaymentHistory | EP | 1–2×payment | transiciones coherentes |
| Tasks | Task | T | ~count | board_type/estado variados |
| Tasks | TaskAlert | T | ~40% tasks | FK task |
| Tasks | TaskComment | T | ~50% tasks | FK task/author |
| Auth | UserProfile | SP/DC | admin + clientes | roles, onboarding |
| Auth | VerificationCode | — | efímero | no se siembra (OTP runtime) |
| Settings | CompanySettings | EP | 1 (pk=1) | singleton |
| Settings | ConfidentialityTemplate / ContractTemplate | M/P | default | plantillas |
| Settings | EmailTemplateConfig | EP | 2 | overrides |
| Settings | ProposalDefaultConfig / DiagnosticDefaultConfig | M/EP | por idioma | singleton por lang |
| Settings | SavedFilterTab | EP | 2 (admin) | tabs de filtro |
| Settings | LinkedInToken | — | n/a | token real (no fake) |
| Web Form | Contact | create_contacts | ~count | formulario público |

## Notas de mantenimiento

- **Orden de dependencias:** `seed_platform_data` debe correr antes que
  `create_fake_documents` (las cuentas de cobro necesitan clientes/proyectos) y
  antes que `enrich_platform_data` (enriquece pagos/entregables existentes).
- **Idempotencia:** los comandos saltan si ya hay datos suficientes; para regenerar
  desde cero usar `delete_fake_data --confirm` primero.
- **Catálogos preservados** por `delete_fake_data`: `DocumentType`, `IssuerProfile`,
  plantillas de contrato/confidencialidad, y cuentas superuser/staff.
- **Modelos sin fake data a propósito:** `VerificationCode` (OTP efímero) y
  `LinkedInToken` (token OAuth real, cifrado).
