"""One-off command to replace the Hosting badge in whatsIncluded with Entrega y despliegue."""

from django.core.management.base import BaseCommand

from content.models.proposal_section import ProposalSection


class Command(BaseCommand):
    help = "Update whatsIncluded badge from Hosting to Entrega y despliegue in all investment sections."

    def handle(self, *_args, **_options):
        sections = ProposalSection.objects.filter(section_type="investment")
        updated = 0
        for section in sections:
            cj = section.content_json or {}
            items = cj.get("whatsIncluded", [])
            changed = False
            for idx, item in enumerate(items):
                if isinstance(item, str):
                    text = item.lower()
                    if "hosting" in text or "cloud" in text:
                        items[idx] = {
                            "icon": "\U0001f4e6",
                            "title": "Entrega y despliegue",
                            "description": "Despliegue en producción y puesta en marcha",
                        }
                        changed = True
                elif isinstance(item, dict):
                    title = (item.get("title") or "").lower().strip()
                    if "hosting" in title or "cloud" in title:
                        item["icon"] = "\U0001f4e6"
                        item["title"] = "Entrega y despliegue"
                        item["description"] = "Despliegue en producción y puesta en marcha"
                        changed = True
            if changed:
                cj["whatsIncluded"] = items
                section.content_json = cj
                section.save(update_fields=["content_json"])
                updated += 1
                self.stdout.write(
                    f"  Updated section {section.pk} (proposal: {section.proposal})"
                )

        self.stdout.write(
            self.style.SUCCESS(f"Done. Updated {updated} investment section(s).")
        )
