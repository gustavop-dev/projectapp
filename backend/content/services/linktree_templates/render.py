"""Server-side renderer. Only trusted platform code is executable."""
import copy
import hashlib
import html
import json
import re
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree

import html5lib
from django.conf import settings
from django.core import signing

from .syntax import TAGS, TemplateError, issue, render_mustache, rewrite_css


def safe_url(value):
    value = (value or '').strip()
    if not value or any(ord(c) < 32 or c == '\\' for c in value):
        return ''
    try:
        url = urlsplit(value)
        if url.scheme in {'https', 'http'} and url.hostname and not url.username and not url.password:
            return value
        if url.scheme in {'mailto', 'tel'} and url.path and not re.search(r'%0[ad]', value, re.I):
            return value
    except ValueError:
        pass
    return ''


def profile_data(tree):
    buttons = []
    for button in tree.buttons.all():
        if not button.is_active or button.kind in {'download-vcard', 'pwa-install'} or not button.href:
            continue
        href = safe_url(button.href)
        if not href:
            issue(f'El enlace «{button.label}» tiene una URL inválida.', 'profile', code='profile_url')
        kind = ('email' if href.startswith('mailto:') else 'phone' if href.startswith('tel:') else
                'whatsapp' if button.action == 'whatsapp' else 'social' if button.action in {'instagram', 'linkedin'} else
                'file' if re.search(r'\.(?:pdf|docx?|xlsx?|zip)(?:\?|$)', href, re.I) else 'web')
        buttons.append({'label': button.label, 'url': href, 'icon': button.resolved_icon,
                        'kind': kind, 'key': str(button.pk), 'tier': button.tier})
    base = getattr(settings, 'FRONTEND_URL', 'https://projectapp.co').rstrip('/')
    # Public URLs never derive from a user-supplied Host header.
    if not safe_url(base):
        base = 'https://projectapp.co'
    return {'name': tree.display_name or tree.name, 'role': tree.role, 'bio': tree.bio,
            'company': tree.vcard_org, 'badge': tree.badge_text, 'footer_tagline': tree.footer_tagline,
            'profile_url': f'{base}{tree.public_path}', 'photo_url': tree.avatar.name if tree.avatar else '',
            'logo_url': tree.logo.name if tree.logo else '', 'buttons': buttons,
            'contact': {key: getattr(tree, f'vcard_{key}') for key in ('first_name', 'last_name', 'org', 'email', 'tel', 'url')},
            'pwa_enabled': tree.pwa_enabled}


def profile_digest(profile):
    return hashlib.sha256(json.dumps(profile, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def asset_url(version, key, density=1):
    return f'/api/linktrees/templates/{version.id}/assets/{key}/{density}/'


def asset_token(version):
    return signing.dumps(str(version.id), salt='linktree-template-preview')


def font_url(fonts):
    if not fonts:
        return ''
    return 'https://fonts.googleapis.com/css2?' + '&'.join(f'family={quote(font, safe=":;,@")}' for font in fonts) + '&display=swap'


@lru_cache(maxsize=1)
def icon_catalog():
    vendor = Path(__file__).parent / 'vendor'
    return {**json.loads((vendor / 'lucide.json').read_text()),
            **json.loads((vendor / 'legacy-icons.json').read_text())}



class SourceMarkers(HTMLParser):
    """Trusted markers preserve source lines and link identity through loops."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        insertion = f' data-template-line="{self.getpos()[0]}"'
        if tag == 'a' and 'data-link' in dict(attrs):
            insertion += ' data-link-key="{{__platform_link_key}}"'
        end = -2 if raw.endswith('/>') else -1
        self.parts.append(raw[:end] + insertion + raw[end:])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f'&{name};')

    def handle_charref(self, name):
        self.parts.append(f'&#{name};')

    def handle_comment(self, data):
        self.parts.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self.parts.append(f'<!{decl}>')


def render_document(version):
    template, profile = version.template, copy.deepcopy(version.profile)
    urls = {key: asset_url(version, key) for key in version.assets}
    profile['photo_url'] = urls.get('slot-photo', '')
    profile['logo_url'] = urls.get('slot-logo', '')
    profile['initials'] = ''.join(part[0] for part in profile['name'].split()[:2]).upper()
    links = profile.pop('buttons')
    primary = next((link for link in links if link['tier'] == 'primary'), None)
    if re.search(r'{{\s*#\s*primary_link\s*}}', template.html):
        links = [link for link in links if link is not primary]
    def numbered(items):
        return [{**item, '__platform_link_key': item['key'], 'index': i, 'first': i == 0, 'last': i == len(items) - 1} for i, item in enumerate(items)]
    profile['primary_link'] = numbered([primary])[0] if primary else None
    profile['links'] = numbered(links)
    for kind in ('web', 'whatsapp', 'email', 'phone', 'social', 'file'):
        profile[f'links.{kind}'] = numbered([link for link in links if link['kind'] == kind])
    marked = SourceMarkers(); marked.feed(template.html)
    document = html5lib.parse(render_mustache(''.join(marked.parts), profile, frozenset({'__platform_link_key'})), namespaceHTMLElements=False)
    # A second structural check closes malformed-HTML/parser differential cases.
    for index, element in enumerate(document.iter()):
        if not isinstance(element.tag, str):
            continue
        if element.tag not in TAGS:
            issue('El HTML genera un elemento no permitido.')
        element.set('data-template-node', str(index))
        if element.tag == 'style':
            element.text = rewrite_css(element.text or '', urls)
        if element.get('style'):
            element.set('style', rewrite_css(element.get('style'), urls))
        key = element.get('data-asset')
        if key:
            asset = version.assets[key]
            element.set('src', urls[key])
            element.set('srcset', ', '.join(f'{asset_url(version, key, d)} {d}x' for d in (1, 2, 3)))
            element.set('alt', asset.get('alt', ''))
            if not asset.get('alt'):
                element.set('aria-hidden', 'true')
        if element.tag == 'img' and not key:
            for slot in ('photo', 'logo'):
                if element.get('src') and element.get('src') == urls.get(f'slot-{slot}'):
                    element.set('srcset', ', '.join(f'{asset_url(version, f"slot-{slot}", d)} {d}x' for d in (1, 2, 3)))
                    aspect = template.manifest.get('slots', {}).get(slot, {}).get('aspect')
                    if aspect:
                        element.set('style', (element.get('style') or '') + ';aspect-ratio:' + aspect.replace(':', '/') + ';object-fit:cover')
            if not element.get('src'):
                element.set('hidden', '')
        if element.tag == 'a' and element.get('href'):
            if not safe_url(element.get('href')):
                issue('El perfil produjo un enlace no permitido.', 'profile')
            element.set('rel', 'noopener noreferrer')
            element.set('target', '_top')
            link = next((b for b in version.profile['buttons'] if b['key'] == element.get('data-link-key') and b['url'] == element.get('href')), None)
            if not link:
                issue('El enlace no pertenece a este perfil.')
            element.set('data-link-key', link['key'])
        action = element.get('data-action')
        contact = version.profile['contact']
        if ((action == 'whatsapp' and not re.sub(r'\D', '', contact['tel'])) or
            (action == 'email' and not contact['email']) or action == 'install-pwa'):
            element.set('hidden', '')
        if element.tag == 'button':
            element.set('type', 'button')
    # Insert only vendored, trusted SVG after validating the author's HTML tree.
    for element in list(document.iter()):
        name = element.get('data-icon')
        if name:
            svg = icon_catalog().get(name)
            if not svg:
                issue(f'Icono Lucide desconocido: {name}.')
            icon = ElementTree.fromstring(svg)
            icon.set('aria-hidden', 'true'); icon.set('width', '1em'); icon.set('height', '1em')
            element.append(icon)
    head = document.find('head')
    ElementTree.SubElement(head, 'meta', {'charset': 'utf-8'})
    ElementTree.SubElement(head, 'meta', {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'})
    title = head.find('title')
    if title is None:
        title = ElementTree.SubElement(head, 'title')
    title.text = version.profile['name']
    description = (version.profile.get('bio') or version.profile.get('role') or version.profile['name'])[:160]
    ElementTree.SubElement(head, 'meta', {'name': 'description', 'content': description})
    if version.profile.get('profile_url'):
        ElementTree.SubElement(head, 'link', {'rel': 'canonical', 'href': version.profile['profile_url']})
    ElementTree.SubElement(head, 'meta', {'property': 'og:title', 'content': version.profile['name']})
    ElementTree.SubElement(head, 'meta', {'property': 'og:description', 'content': description})
    # A zero-margin baseline preserves the actual 320px canvas without masking overflow.
    baseline = ElementTree.Element('style')
    baseline.text = 'html,body{margin:0}*,*::before,*::after{box-sizing:border-box}[hidden]{display:none!important}body{max-width:' + str(template.manifest['max_width']) + 'px;margin-inline:auto}svg{vertical-align:middle}'
    head.insert(0, baseline)
    url = font_url(template.manifest['fonts'])
    if url:
        ElementTree.SubElement(head, 'link', {'rel': 'stylesheet', 'href': url})
    style = ElementTree.SubElement(head, 'style'); style.text = rewrite_css(template.css, urls)
    return '<!doctype html>' + html5lib.serialize(document, tree='etree', quote_attr_values='always', omit_optional_tags=False)


def preview_document(version):
    token = quote(asset_token(version), safe='')
    document = version.document
    for key in version.assets:
        for density in (1, 2, 3):
            url = asset_url(version, key, density)
            document = document.replace(url, f'{url}?preview={token}')
    return document


def public_document(version, nonce):
    runtime = (Path(__file__).parent / 'runtime.js').read_text()
    data = {'version': str(version.id), 'profile': version.profile,
            'click_url': f'/api/linktrees/templates/{version.id}/click/'}
    encoded = json.dumps(data, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    script = f'<script nonce="{html.escape(nonce, quote=True)}">(({runtime})({encoded}));</script>'
    document = version.document
    if version.profile.get('pwa_enabled'):
        manifest = f'/api/linktrees/public/{version.linktree.handle}/manifest.webmanifest'
        document = document.replace('</head>', f'<link rel="manifest" href="{manifest}"></head>')
    return document.replace('</body>', script + '</body>')


def content_security_policy(nonce=None, preview=False):
    script = f"'nonce-{nonce}'" if nonce else "'none'"
    policy = (f"default-src 'none'; script-src {script}; script-src-attr 'none'; "
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
              "img-src 'self'; font-src 'self' https://fonts.gstatic.com; "
              "connect-src 'self'; worker-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; "
              "frame-ancestors 'self'")
    if preview:
        policy += '; sandbox'
    return policy
